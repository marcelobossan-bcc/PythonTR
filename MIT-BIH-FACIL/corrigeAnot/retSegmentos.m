function [segs,t,classes,n] = retSegmentos( sinal,anotacoes,tJanela,filtro)
% Retorna segmentos de sinais com duração tJanela (ms) centralizados
% nas anotaçoes correspondentes a classificação de batimentos
% t retorna a base de tempo

npts=floor(360*tJanela/1000);
npts2=npts/2;
npts32=1.5*npts;

t=(0:npts)/360;

Bftr=ones(10,1);
Aftr=1;

if(filtro)
    sinal=filtfilt(Bftr,Aftr,sinal);
end

sinal=[ones(npts,1)*sinal(1);sinal;ones(npts,1)*sinal(length(sinal))];

anot=filtraqrs(anotacoes);
classes=unique(anot(:,1));
l=length(classes);
n=zeros(l,1);

for i=1:l    
    B=anot(anot(:,1)==classes(i),:);
    n(i)=length(B(:,1));
    for k=1:n(i)
        s2=sinal(B(k,2)+npts2:B(k,2)+npts32)';
        s2=s2-min(s2);
        s2=s2/max(s2);
        segs(i,k,:)=s2;
    end
end


