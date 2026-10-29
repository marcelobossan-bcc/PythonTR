% Script de exemplo do uso da base MIT-BIH-FACIL

clear all
close all

npts=5000;
t=[0:npts-1]/360;

% Leitura do Sinal

Y=wavread('sinais\100.wav','native');
s1=escala(Y(1:npts,1));
s2=escala(Y(1:npts,2));

% Leitura das anotações

fid=fopen('anotações\100.ant');
A=fscanf(fid,'%d',[2,inf])';
fclose(fid);

anot=A(find(A(:,2)<5000),:);

anot=filtraqrs(anot);

% Desenho dos gráficos

figure(1)
hold on
subplot(211),plot(t,s1);
text(anot(:,2)/360,zeros(1,length(anot(:,2))),categoria(anot(:,1)))
hold off
title('derivação 1');
xlabel('segundos');
ylabel('mV');

hold on
subplot(212),plot(t,s2);
title('derivação 2');
text(anot(:,2)/360,zeros(1,length(anot(:,2))),categoria(anot(:,1)))
hold off
xlabel('segundos');
ylabel('mV');
