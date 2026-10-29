function sinalMv = escala(sinal)
% sinalMv = escala(sinal)
% Esta função recebe um sinal inteiro, lido da base de dados MIT-BIH,
% e o converte para um sinal ponto flutuante, escalado em mV

sinalMv=double(sinal-1024)/200.0;

end

