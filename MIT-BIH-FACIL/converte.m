% Este programa converte os dados da base MIT-BIH para um formato de 
% uso mais simples. 
%
% Os arquivos de sinais são convertidos para o formato
% WAVE, com dois canais e taxa de amostragem de 360 amostras/s. 
% As amostras são salvas em 16 bits, a partir dos 11 bits originais.
% A amplitude 0 corresponde ao valor 1024
% Exemplo de leitura:
% Y=wavread('100.wav','native'); 
% onde Y é uma matriz com duas colunas, contendo os dois canais de ECG. 
% Para converter os valores para mV, basta subtrair de cada amostra
% o valor 1024 e dividir o resultado por 200.
%
% Os arquivos de anotação são convertidos para o formato texto de duas
% colunas, separadas por espaço, a primeira contendo o índice da anotação
% segundo o arquivo ecgcodes.h e, a segunda, com o número da amostra
% correspondente à anotação, contada a partir do início de gravação, 
% amostra 0.
% Exemplo de leitura:
% fid=fopen('100.ant','r');A=fscanf(fid,'%d',[2,inf]);fclose(fid);
% onde A é uma matriz com duas colunas, a primeira com os códigos e, a
% segunda, com as posições das anotações.
%
% Criado por Marcelo C. Bossan em 18/04/2017, 
% baseado em outro programa desenvolvido por Robert Tratnig 
% (Vorarlberg University of Applied Sciences)(email: rtratnig@gmx.at),
%

% Definições

clc; clear all;

PATH_ANOTACOES_ORIG = '..\MIT-BIH\anotações';
PATH_SINAIS_ORIG = '..\MIT-BIH\sinais';

PATH_ANOTACOES_DEST = 'anotações';
PATH_SINAIS_DEST = 'sinais';

nomes = [100 101 102 103 104 105 106 107 108 109 111 112 ...
         113 114 115 116 117 118 119 121 122 123 124 200 ...
         201 202 203 205 207 208 209 210 212 213 214 215 ...
         217 219 220 221 222 223 228 230 231 232 233 234];

% Processamento

for i=1:length(nomes)
    
    % Convertendo sinal
    
    origem=sprintf('%s\\%d.dat',PATH_SINAIS_ORIG,nomes(i));
    fid=fopen(origem,'r');
    clear A;
    A=fread(fid,[3, inf],'uint8')';
    fclose(fid);
    
    M2H= bitshift(A(:,2), -4);
    M1H= bitand(A(:,2), 15);
    PRL=bitshift(bitand(A(:,2),8),9);
    PRR=bitshift(bitand(A(:,2),128),5);
    M( : , 1)= int16(bitshift(M1H,8)+ A(:,1)-PRL);
    M( : , 2)= int16(bitshift(M2H,8)+ A(:,3)-PRR);
    
    destino=sprintf('%s\\%d.wav',PATH_SINAIS_DEST,nomes(i));
    wavwrite(M,360,16,destino);
    
    % Convertendo anotação

    origem=sprintf('%s\\%d.atr',PATH_ANOTACOES_ORIG,nomes(i));
    fid=fopen(origem,'r');
    clear A;
    A= fread(fid, [2, inf], 'uint8')';
    fclose(fid);    
    
    ATRTIME=[];
    ANNOT=[];
    sa=size(A);
    saa=sa(1);
    k=1;
    while k<=saa
        annoth=bitshift(A(k,2),-2);
        if annoth==59
            ANNOT=[ANNOT;bitshift(A(k+3,2),-2)];
            ATRTIME=[ATRTIME;A(k+2,1)+bitshift(A(k+2,2),8)+...
                    bitshift(A(k+1,1),16)+bitshift(A(k+1,2),24)];
            k=k+3;
        elseif annoth==60
            % nothing to do!
        elseif annoth==61
            % nothing to do!
        elseif annoth==62
            % nothing to do!
        elseif annoth==63
            hilfe=bitshift(bitand(A(k,2),3),8)+A(k,1);
            hilfe=hilfe+mod(hilfe,2);
            k=k+hilfe/2;
        else
            ATRTIME=[ATRTIME;bitshift(bitand(A(k,2),3),8)+A(k,1)];
            ANNOT=[ANNOT;bitshift(A(k,2),-2)];
       end;
       k=k+1;
    end;

    N=[ANNOT cumsum(ATRTIME)]';
    
    N=N(:,1:length(ANNOT)-1);
    
    destino=sprintf('%s\\%d.ant',PATH_ANOTACOES_DEST,nomes(i));
    fid=fopen(destino,'w');  
    fprintf(fid,'%3d %7d\n',N);
    fclose(fid);  
end
