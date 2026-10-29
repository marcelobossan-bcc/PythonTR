############################################################################
#                                                                          #
#       Aulas de REALTIME PYTHON   (PEB/COPPE/UFRJ)                        #
#                                                                          #
#       Exemplo2: Exibição de ECG em tempo real  (ecg1.py)                 #
#       usa o MIT-BIH-FACIL (mod do MIT-BIH distribuído pela Physinet      #
#                                                                          #
#       Requer a biblioteca pyqtgraph (cria uma aplicação QtWidgets)       #
#                                                                          #
#       Marcelo C Bossan, D.Sc.                                            #
#                                                                          #
#       Outubro/2026                                                       #
#                                                                          #
############################################################################

import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
import numpy as np
import wave
import sys

# Abre o arquivo wave de 2 canais e extrai os sinais individualmente
def carregar_canais_ecg(caminho_arquivo):
    with wave.open(caminho_arquivo, 'rb') as wf:
        n_canais = wf.getnchannels()
        n_frames = wf.getnframes()
        
        dados_brutos = wf.readframes(n_frames)
        sinal_intercalado = np.frombuffer(dados_brutos, dtype=np.int16)
        canal1 = sinal_intercalado[0::n_canais]
        canal2 = sinal_intercalado[1::n_canais]
        
        return canal1, canal2

# Classe principal
class MonitorECGDoisCanais(QtWidgets.QMainWindow):
    def __init__(self, caminho_wav):
        super().__init__()
        
        # Configurações de dados e amostragem
        self.c1_total, self.c2_total = carregar_canais_ecg(caminho_wav)
        self.indice_leitura = 0
        self.frequencia_hz = 360  
        
        # Janela de 4 segundos na tela (360 * 4 = 1440 amostras)
        self.tamanho_janela_pontos = 1440 
        
        # Inicializa ambos os vetores de tela vazios usando NaN
        self.c1_tela = np.full(self.tamanho_janela_pontos, np.nan)
        self.c2_tela = np.full(self.tamanho_janela_pontos, np.nan)
        self.ponteiro_tela = 0  
        
        # Configura o layout e gráficos da interface
        self.init_ui()
        
        # Otimização gráfica: atualiza em blocos de 6 amostras (60 FPS)
        self.amostras_por_ciclo = 6  
        intervalo_timer_ms = int((1000 / self.frequencia_hz) * self.amostras_por_ciclo)
        
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.atualizar_graficos)
        self.timer.start(intervalo_timer_ms)

    def init_ui(self):
        self.setWindowTitle("Monitor de ECG - Duas Derivações (360 Hz)")
        self.resize(1000, 650)
        
        # Widget e Layout para organizar os dois gráficos um em cima do outro
        widget_central = QtWidgets.QWidget()
        self.setCentralWidget(widget_central)
        layout = QtWidgets.QVBoxLayout(widget_central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Criação das duas áreas de plotagem independentes
        self.plot_c1 = pg.PlotWidget()
        self.plot_c2 = pg.PlotWidget()
        
        layout.addWidget(self.plot_c1)
        layout.addWidget(self.plot_c2)
        
        # Configurações visuais comuns para ambas as telas
        for grafico, titulo in [(self.plot_c1, "Canal 1"), 
                                (self.plot_c2, "Canal 2")]:
            grafico.setBackground('k')
            grafico.showGrid(x=True, y=True, alpha=0.15)
            grafico.setXRange(0, self.tamanho_janela_pontos)
            grafico.setLabel('bottom', 'Tempo', units='Amostras')
            grafico.setTitle(titulo, color='w', size='10pt')
            
        # Vincula o zoom do eixo X de uma tela à outra de forma síncrona
        self.plot_c2.setXLink(self.plot_c1)
        
        # Define os limites verticais estáticos de Y baseados na amplitude máxima de cada sinal
        self.plot_c1.setYRange(int(np.min(self.c1_total)) - 50, int(np.max(self.c1_total)) + 50)
        self.plot_c2.setYRange(int(np.min(self.c2_total)) - 50, int(np.max(self.c2_total)) + 50)
        
        # Configura as cores e larguras de curva
        pen_c1 = pg.mkPen(color='#00FF00', width=2)
        pen_c2 = pg.mkPen(color='#FFFF00', width=2)
        
        # Desenha as curvas iniciais (zeradas por conta dos nan)
        self.curva_c1 = self.plot_c1.plot(self.c1_tela, pen=pen_c1)
        self.curva_c2 = self.plot_c2.plot(self.c2_tela, pen=pen_c2)

    def atualizar_graficos(self):
        # Determina o limite mínimo de dados restantes entre os dois canais
        limite_dados = min(len(self.c1_total), len(self.c2_total))
        
        # Reinicia o arquivo em loop se chegar ao fim das amostras
        if self.indice_leitura + self.amostras_por_ciclo >= limite_dados:
            self.indice_leitura = 0
            
        # Extrai os pacotes paralelos de dados de ambos os canais
        novas_amostras_c1 = self.c1_total[self.indice_leitura : self.indice_leitura + self.amostras_por_ciclo]
        novas_amostras_c2 = self.c2_total[self.indice_leitura : self.indice_leitura + self.amostras_por_ciclo]
        self.indice_leitura += self.amostras_por_ciclo
        
        # Adiciona novos pontos na posição do ponteiro
        for i in range(self.amostras_por_ciclo):
            if self.ponteiro_tela >= self.tamanho_janela_pontos:
                self.ponteiro_tela = 0
                
            self.c1_tela[self.ponteiro_tela] = novas_amostras_c1[i]
            self.c2_tela[self.ponteiro_tela] = novas_amostras_c2[i]
            self.ponteiro_tela += 1
            
        # Cria a barra escura de apagamento à frente da linha (efeito varredura/sweep)
        tamanho_apagamento = 45
        for idx in range(tamanho_apagamento):
            pos_apagamento = (self.ponteiro_tela + idx) % self.tamanho_janela_pontos
            self.c1_tela[pos_apagamento] = np.nan
            self.c2_tela[pos_apagamento] = np.nan
            
        # Atualiza as duas linhas na interface gráfica
        self.curva_c1.setData(self.c1_tela)
        self.curva_c2.setData(self.c2_tela)

if __name__ == '__main__':
    # Altere para o caminho do seu arquivo de sinais do MIT-BIH-FACIL
    arquivo_ecg_estereo = "../MIT-BIH-FACIL/sinais/100.wav" 
    
    app = QtWidgets.QApplication(sys.argv)
    
    try:
        monitor = MonitorECGDoisCanais(arquivo_ecg_estereo)
        monitor.show()
        sys.exit(app.exec_())
    except FileNotFoundError:
        print(f"Erro: O arquivo '{arquivo_ecg_estereo}' não foi encontrado.")
