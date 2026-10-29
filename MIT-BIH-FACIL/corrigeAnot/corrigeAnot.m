% Este programa foi desenvolvido com o objetivo de permitir a remarcação
% das anotações de batimentos cardíacos do MIT-BIH-FACIL. As marcações
% originais apresentam algumas inconsistências de localização resultantes
% do processo utilizado para a detecção das ondas R dos batimentos, que foi
% a aplicação de um filtro passa-baixo seguida de uma detecção de máximo.
%
% No programa corrigeAnot, é possível definir um batimento como referência
% e utilizá-lo para detectar a localização dos demais batimentos por
% correlação. Um campo de coeficiente de correlação mínimo permite 
% definir o mínimo de correlação que deve existir entre os batimentos
% do arquivo e o batimento de referência para qu a correção seja aplicada,
% possibilitando correções pontuais no caso de arquivos com classes 
% multiformes, como o que acontece no caso de PVCs multifocais.
%
% Para evitar o comprometimento das anotações originais, todo o
% processamento é realizado em uma posta chamada anotações_mod, que deve
% ser criada pelo usuário e para a qual todos os arquivos de anotações
% originais devem ser transferidos. Esses arquivos serão alterados quando o
% botão salva da aplicação for selecionado.
%
% Assim como em todos os aplicativos deste pavote, é fundamental que a
% pasta MIT-BIH-FACIL\funções esteja no PATH do matlab antes de sua 
% execução.


% Criado por Marcelo C. Bossan em 03/05/2017, 

function varargout = corrigeAnot(varargin)

% Begin initialization code - DO NOT EDIT
gui_Singleton = 1;
gui_State = struct('gui_Name',       mfilename, ...
                   'gui_Singleton',  gui_Singleton, ...
                   'gui_OpeningFcn', @corrigeAnot_OpeningFcn, ...
                   'gui_OutputFcn',  @corrigeAnot_OutputFcn, ...
                   'gui_LayoutFcn',  [] , ...
                   'gui_Callback',   []);
if nargin && ischar(varargin{1})
    gui_State.gui_Callback = str2func(varargin{1});
end

if nargout
    [varargout{1:nargout}] = gui_mainfcn(gui_State, varargin{:});
else
    gui_mainfcn(gui_State, varargin{:});
end
% End initialization code - DO NOT EDIT


function varargout = corrigeAnot_OutputFcn(~, ~, handles) 
% --- Outputs from this function are returned to the command line.

varargout{1} = handles.output;

function corrigeAnot_OpeningFcn(hObject, ~, handles, varargin)
% inicialização de variáveis

handles.output = hObject;

handles.PATH_ANOTACOES = '..\anotações_mod';
handles.PATH_SINAIS = '..\sinais';

handles.tJanela=500;        %duração da janela de visão de QRS em ms
handles.tBusca=150;         %duração da janela de busca em ms

handles.loop=0;

handles.nptsJanela=floor(360*handles.tJanela/1000);
handles.nptsBusca=floor(360*handles.tBusca/1000);
handles.centroBusca=handles.nptsJanela/2+1;

handles.novaAnot=0;

handles=AtualizaGrfOrig(hObject,handles,1);

guidata(hObject, handles);


function popClasse_Callback(hObject, ~, handles)
% processa o combobox de seleção de classe de batimentos

processando(handles,1)

classeAtiva=get(hObject,'Value');

plot(handles.grfOrig,handles.t,squeeze(handles.segs(classeAtiva,:,:)));
set(gca,'YTick',[])

AtualizaNumQrs(hObject,handles);
set(handles.campoQRS,'String',1);

handles.referencia=squeeze(handles.segs(classeAtiva,1,:));

P1=handles.anot(:,1)==handles.classes(classeAtiva);
P2=handles.anot(P1,2);
handles.anotRef=P2(1);
atualizaReferencia(handles,1)

handles=limpaGrfProc(hObject,handles);

processando(handles,0)
guidata(hObject, handles);

function popClasse_CreateFcn(hObject, ~, ~)
% --- Executes during object creation, after setting all properties.

if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

function popPaciente_Callback(hObject, ~, handles)
% processa o combobox de seleção de paciente

processando(handles,1)

handles=AtualizaGrfOrig(hObject,handles,1);
AtualizaNumQrs(hObject,handles)

classeAtiva=get(handles.popClasse,'value');

handles.referencia=squeeze(handles.segs(classeAtiva,1,:));

P1=handles.anot(:,1)==handles.classes(classeAtiva);
P2=handles.anot(P1,2);
handles.anotRef=P2(1);

atualizaReferencia(handles,1)

processando(handles,0)

guidata(hObject, handles);

function popPaciente_CreateFcn(hObject, ~, ~)
% inicialização do combobox de pacientes

if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end
   
nomes = [100 101 102 103 104 105 106 107 108 109 111 112 ...
     113 114 115 116 117 118 119 121 122 123 124 200 ...
     201 202 203 205 207 208 209 210 212 213 214 215 ...
     217 219 220 221 222 223 228 230 231 232 233 234];

set(hObject,'string',nomes);

function pbSalva_Callback(~, ~, handles)
% salva o arquivo

contents=cellstr(get(handles.popPaciente,'String'));
arquivoAnot=sprintf('%s\\%s.ant',handles.PATH_ANOTACOES,contents{get(handles.popPaciente,'Value')});
fid=fopen(arquivoAnot,'w'); 
fprintf(fid,'%3d %7d\n',handles.anot');

fclose(fid);  

function pbDec1_Callback(hObject, ~, handles)
% decrementa a referência 1 batimento

handles=incrementaReferencia(handles,hObject,-1);
guidata(hObject, handles);

function pbInc1_Callback(hObject, ~, handles)
% incrementa a referência 1 batimento

handles=incrementaReferencia(handles,hObject,1);
guidata(hObject, handles);

function pbDec10_Callback(hObject, ~, handles)
% loop de decremento de referência

handles.loop=1;
guidata(hObject, handles);

while handles.loop==1
    handles2=incrementaReferencia(handles,hObject,-1);
    handles = guidata(hObject);
end
guidata(hObject, handles2);

function pbInc10_Callback(hObject, ~, handles)
% loop de incremento de referência

handles.loop=1;
guidata(hObject, handles);
    
while handles.loop==1
    handles2=incrementaReferencia(handles,hObject,1);
    handles = guidata(hObject);
end
guidata(hObject, handles2);

function refNum_CreateFcn(hObject, ~, ~)
% inicializa o campo contador da referência

if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

function ccmin_Callback(hObject, ~, handles)
% corrige o campo de coeficiente de correlação mínimo se não numérico

valorStr=get(hObject,'String');
valor=str2double(valorStr);

if(isnan(valor))||length(find(valorStr==','))
    set(hObject,'String',num2str(handles.rmin));
else
   handles.rmin=valor; 
end
guidata(hObject, handles);

function ccmin_CreateFcn(hObject, ~, ~)
% inicializa o campo de coeficiente de correlação

if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

function pbSinc_Callback(hObject, ~, handles)
% executa a sincronização

processando(handles,1)

classeAtiva=get(handles.popClasse,'value');
ccmin=str2double(get(handles.ccmin,'String'));

% filtro casado

p1=handles.centroBusca-handles.nptsBusca/2;
p2=handles.centroBusca+handles.nptsBusca/2;

sinald=detrend(squeeze(handles.segs(classeAtiva,:,:))','constant')';

refd=fliplr(detrend(handles.referencia(p1:p2),'constant')');

saida=filter(refd,1,sinald')'./length(refd);

% normaliza picos pelos desvios padrões

[ma,pm]=max(saida,[],2);
l=handles.nc(classeAtiva);

dpRefd=std(refd);

p1=pm-handles.nptsBusca;
p2=pm;
ccoef=zeros(l,1);
for i=1:l
    if (p1(i)>0)&&(p2(i)>0)
        ccoef(i)=ma(i)./(std(sinald(i,p1(i):p2(i)))*dpRefd);
    else
        ccoef(i)=0;
    end
end

% calcula os desvios de sinc

desvio=pm-handles.nptsBusca/2-handles.nptsJanela/2-2;

% gera tabela de alinhamento alternativa 

handles.anot2=handles.anot;
P1=handles.anot2(:,1)==handles.classes(classeAtiva);
P2=ccoef>=ccmin;
correcao=zeros(size(ccoef));
correcao(P2)=desvio(P2);
handles.anot2(P1,2)=handles.anot2(P1,2)+correcao;

% plota os batimentos realinhados

handles=atualizaGrfProc(hObject,handles);

processando(handles,0)
guidata(hObject, handles);

function pbTrans_Callback(hObject, ~, handles)
% transfere a tabela de anotação alternativa para a tabela original
% e atualiza o gráfico

classeAtiva=get(handles.popClasse,'value');

if handles.novaAnot==1

    % atualiza batimentos sincronizados
    processando(handles,1)

    handles.anot=handles.anot2;
    filtro=get(handles.filtro,'Value');

    if(get(handles.popDeriv,'Value')==1)
        [handles.segs,handles.t,handles.classes,handles.nc]= ...
                retSegmentos(handles.deriv1,handles.anot,handles.tJanela,filtro);
    else
        [handles.segs,handles.t,handles.classes,handles.nc]= ...
                retSegmentos(handles.deriv2,handles.anot,handles.tJanela,filtro);    
    end
    
    handles=limpaGrfProc(hObject,handles);

    processando(handles,0)
else
    % salva gráfico e posição de referência

    numQRS=str2double(get(handles.campoQRS,'String'));
    P1=cumsum(handles.anot(:,1)==handles.classes(classeAtiva));
    pos=find(P1==numQRS,1,'first');
    handles.anot(pos,2)=handles.anotRef;
    handles.segs(classeAtiva,numQRS,:)=handles.referencia;
end

plot(handles.grfOrig,handles.t,squeeze(handles.segs(classeAtiva,:,:)));
set(gca,'YTick',[])

guidata(hObject, handles);


function handles=AtualizaGrfOrig(hObject,handles,reset)
% Atualiza a tela gráfica original

contents=cellstr(get(handles.popPaciente,'String'));

if(reset)
    arquivoAnot=sprintf('%s\\%s.ant',handles.PATH_ANOTACOES,contents{get(handles.popPaciente,'Value')});
    fid=fopen(arquivoAnot);
    handles.anot=fscanf(fid,'%d',[2,inf])';
    fclose(fid);
    
    handles.anot2=handles.anot;

    arquivoSinais=sprintf('%s\\%s.wav',handles.PATH_SINAIS,contents{get(handles.popPaciente,'Value')});
    Y=wavread(arquivoSinais,'native');
    handles.deriv1=escala(Y(:,1));
    handles.deriv2=escala(Y(:,2));
    clear Y;
end

filtro=get(handles.filtro,'Value');

if(get(handles.popDeriv,'Value')==1)
    [handles.segs,handles.t,handles.classes,handles.nc]= ...
            retSegmentos(handles.deriv1,handles.anot,handles.tJanela,filtro);
else
    [handles.segs,handles.t,handles.classes,handles.nc]= ...
            retSegmentos(handles.deriv2,handles.anot,handles.tJanela,filtro);    
end

if(reset)
    set(handles.popClasse,'Value',1);
    set(handles.popClasse,'String',categoria(handles.classes));
end

classeAtiva=get(handles.popClasse,'Value');

plot(handles.grfOrig,handles.t,squeeze(handles.segs(classeAtiva,:,:)));
set(gca,'YTick',[])

handles.referencia=squeeze(handles.segs(classeAtiva,1,:));
set(handles.campoQRS,'String','1');

P1=handles.anot(:,1)==handles.classes(classeAtiva);
P2=handles.anot(P1,2);
handles.anotRef=P2(1);

handles=limpaGrfProc(hObject,handles);

AtualizaNumQrs(hObject,handles)
atualizaReferencia(handles,1)


function handles=atualizaGrfProc(hObject,handles)
% atualiza tela gráfica processado

filtro=get(handles.filtro,'Value');
classeAtiva=get(handles.popClasse,'Value');

if(get(handles.popDeriv,'Value')==1)
    [segs,t,classes,nc]= ...
            retSegmentos(handles.deriv1,handles.anot2,handles.tJanela,filtro);
else
    [segs,t,classes,nc]= ...
            retSegmentos(handles.deriv2,handles.anot2,handles.tJanela,filtro);    
end

plot(handles.grfProc,t,squeeze(segs(classeAtiva,:,:)));
set(gca,'YTick',[])

handles.novaAnot=1;

function handles=limpaGrfProc(hObject,handles)
% limpa a tela gráfica processado
    
cla(handles.grfProc) 
guidata(hObject, handles);
handles.novaAnot=0;

function atualizaReferencia(handles,numQRS)
% atualiza a tela do gráfico de referência

axes(handles.grfRef)

plot(handles.t,handles.referencia);
hold on

p1=handles.centroBusca-handles.nptsBusca/2;
p2=handles.centroBusca+handles.nptsBusca/2;
plot(handles.t(p1:p2),handles.referencia(p1:p2),'r','LineWidth',2);

x=[handles.centroBusca handles.centroBusca]/360;
y=[0 max(handles.referencia)];
line(x,y,'Color','r','LineWidth',2,'LineStyle',':')

hold off

function AtualizaNumQrs(~,handles)
% atualiza os campos de número de QRS de classe e do arquivo

classeAtiva=get(handles.popClasse,'value');
set(handles.campoClasse,'String',handles.nc(classeAtiva));
set(handles.campoTotal,'String',sum(handles.nc));

function processando(handles,visivel)
% torna visível/invisível a mensagem PROCESSANDO

if(visivel)
    set(handles.avisoProc,'Visible','on');
else
    set(handles.avisoProc,'Visible','off'); 
end

drawnow();

function handles=incrementaReferencia(handles,hObject,incremento)
% incrementa/decrementa o gráfico de referência

classeAtiva=get(handles.popClasse,'Value');

valorAtual=str2double(get(handles.campoQRS,'String'));
valor=valorAtual+incremento;
if(valor<1)
    valor=1;
elseif(valor>handles.nc(classeAtiva))
    valor=handles.nc(classeAtiva);
end
set(handles.campoQRS,'String',valor);

handles.referencia=squeeze(handles.segs(classeAtiva,valor,:));

P1=handles.anot(:,1)==handles.classes(classeAtiva);
P2=handles.anot(P1,2);
handles.anotRef=P2(valor);

atualizaReferencia(handles,valor);


function filtro_Callback(hObject, ~, handles)
% ativa/desativa filtro passa baixo

processando(handles,1)
AtualizaGrfOrig(hObject,handles,0)
processando(handles,0)

function popDeriv_Callback(hObject, eventdata, handles)
% processa o combobox de derivação

processando(handles,1)
limpaGrfProc(hObject,handles)
handles.novaAnot=0;
valor=str2double(get(handles.campoQRS,'String'));
handles=AtualizaGrfOrig(hObject,handles,0)

classeAtiva=get(handles.popClasse,'Value');
handles.referencia=squeeze(handles.segs(classeAtiva,valor,:));

P1=handles.anot(:,1)==handles.classes(classeAtiva);
P2=handles.anot(P1,2);
handles.anotRef=P2(valor);

set(handles.campoQRS,'String',valor);

atualizaReferencia(handles,valor);

processando(handles,0)

function popDeriv_CreateFcn(hObject, eventdata, handles)
% inicialização do combobox de derivação

if ispc && isequal(get(hObject,'BackgroundColor'), get(0,'defaultUicontrolBackgroundColor'))
    set(hObject,'BackgroundColor','white');
end

function figure1_WindowButtonDownFcn(hObject, eventdata, handles)
% processa o cursor de centralização da referÊncia
pos = get(gca,'currentpoint');

meiaBusca=handles.nptsBusca*0.25/handles.nptsJanela;

if(pos(1)>(meiaBusca+0.05))&&(pos(1)<=(0.5-meiaBusca))
    handles.centroBusca=round(pos(1)*2*handles.nptsJanela);
    valorAtual=str2double(get(handles.campoQRS,'String'));
    atualizaReferencia(handles,valorAtual);
end
guidata(hObject, handles);   

function PbCent_Callback(hObject, eventdata, handles)
% centraliza a referência

qrs=str2double(get(handles.campoQRS,'String'));
npts2=handles.nptsJanela/2;

handles.anotRef=handles.anotRef+handles.centroBusca-handles.nptsJanela/2;

contents=cellstr(get(handles.popPaciente,'String'));
arquivoSinais=sprintf('%s\\%s.wav',handles.PATH_SINAIS,contents{get(handles.popPaciente,'Value')});
Y=wavread(arquivoSinais,'native');

if(get(handles.popDeriv,'Value')==1)
    sinal=escala(Y(:,1));
else
    sinal=escala(Y(:,2));    
end

sinal=[ones(npts2,1)*sinal(1);sinal;ones(npts2,1)*sinal(length(sinal))];
sinal=sinal(handles.anotRef:handles.anotRef+handles.nptsJanela);
sinal=sinal-min(sinal);
sinal=sinal/max(sinal);
handles.referencia=sinal;

handles.centroBusca=handles.nptsJanela/2;

atualizaReferencia(handles,qrs)

handles=limpaGrfProc(hObject,handles);

hold off
guidata(hObject, handles);

function pushbutton10_Callback(hObject, eventdata, handles)
% interrompe loop de incremento ou decremento

handles.loop=0;
guidata(hObject, handles);

function SalvaGrfOrig_Callback(hObject, eventdata, handles)
% salva o gráfico do eixo ORIGINAL com extenção orig

salvaGrf(handles,'orig');

function SalvaGrfMod_Callback(hObject, eventdata, handles)
% salva o gráfico do eixo ORIGINAL com extenção mod

salvaGrf(handles,'mod');

function salvaGrf(handles,extensao)
% salva grafico

f1 = figure;
pos=get(handles.grfOrig,'Position');
pos(1)=5;pos(2)=2;pos(3)=140;pos(4)=40;
%set(f1,'Position',[10,10,900,250]);
set(f1,'Position',[10,500,900,600]);
eixos_novos = copyobj(handles.grfOrig,f1);
set(eixos_novos,'Position',pos);

contents=cellstr(get(handles.popPaciente,'String'));
classeAtiva=get(handles.popClasse,'value');

arquivo=sprintf('Graficos\\pac%s_%s_%s',contents{get(handles.popPaciente,'Value')},categoria(handles.classes(classeAtiva)),extensao);
print(f1,arquivo,'-dpng')
close Figure 1;

function campoQRS_Callback(hObject, eventdata, handles)
% corrige o campo de contador se não numérico

classeAtiva=get(handles.popClasse,'Value');
valorStr=get(hObject,'String');
valor=str2double(valorStr);

if isnan(valor)||length(find(valorStr==','))
   set(handles.campoQRS,'String','1'); 
else
    if valor<0
        valor=1;
    end
    
    if valor>handles.nc(classeAtiva)
        valor=handles.nc(classeAtiva);
    end

    handles.referencia=squeeze(handles.segs(classeAtiva,valor,:));

    P1=handles.anot(:,1)==handles.classes(classeAtiva);
    P2=handles.anot(P1,2);
    handles.anotRef=P2(valor);

    atualizaReferencia(handles,valor);
end
guidata(hObject, handles);
