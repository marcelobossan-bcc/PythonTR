############################################################################
#                                                                          #
#       Aulas de REALTIME PYTHON   (PEB/COPPE/UFRJ)                        #
#                                                                          #
#       Exemplo3: Exibição de ECG em tempo real + det QRS  (ecg2.py)       #
#       usa o MIT-BIH-FACIL (mod do MIT-BIH distribuído pela Physinet      #
#                                                                          #
#       Requer a biblioteca pyqtgraph (cria uma aplicação QtWidgets)       #
#       e a biblioteca scipy (filtragem digital no detector de QRS)        #
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
from scipy.signal import butter, lfilter

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

# Classe para estimação instantânea da freq. cardíaca via pan-tompkins
class PanTompkinsRR:
    def __init__(self, fs=360):
        self.fs = fs
        nyq = fs / 2
        self.b, self.a = butter(3, [5/nyq, 15/nyq], btype='bandpass')
        self.zi = np.zeros(max(len(self.a), len(self.b)) - 1)
        
        self.tamanho_janela = int(0.150 * fs)
        self.buffer_integracao = np.zeros(self.tamanho_janela)
        self.ultimo_sinal_filtrado = 0.0
        self.limiar = 0.0
        self.ultimo_pico = 0
        self.contador_amostras = 0
        
    def processar_amostra(self, amostra):
        self.contador_amostras += 1
        sf, self.zi = lfilter(self.b, self.a, [amostra], zi=self.zi)
        
        derivada = sf - self.ultimo_sinal_filtrado
        self.ultimo_sinal_filtrado = sf
        
        quadrado = derivada ** 2
        self.buffer_integracao[:-1] = self.buffer_integracao[1:]
        self.buffer_integracao[-1] = quadrado[0]
        valor_integrado = np.mean(self.buffer_integracao)
        
        self.limiar = 0.95 * self.limiar + 0.05 * valor_integrado
        limiar_deteccao = self.limiar * 2.5
        bpm_instantaneo = None
        
        if valor_integrado > limiar_deteccao:
            if (self.contador_amostras - self.ultimo_pico) > 72:
                intervalo_rr_amostras = self.contador_amostras - self.ultimo_pico
                if self.ultimo_pico > 0:
                    bpm_calculado = (60.0 * self.fs) / intervalo_rr_amostras
                    if 40 <= bpm_calculado <= 160:
                        bpm_instantaneo = bpm_calculado
                self.ultimo_pico = self.contador_amostras
                
        return bpm_instantaneo

# Classe principal
class MonitorECGCompleto(QtWidgets.QMainWindow):
    def __init__(self, caminho_wav):
        super().__init__()
        
        # Configurações de dados e amostragem
        self.c1_total, self.c2_total = carregar_canais_ecg(caminho_wav)
        self.indice_leitura = 0
        self.frequencia_hz = 360  
        
        self.total_amostras = min(len(self.c1_total), len(self.c2_total))
        self.duracao_total_segundos = self.total_amostras / self.frequencia_hz
        
        # Variáveis dinâmicas da tela
        self.tamanho_janela_pontos = 1440 
        self.c1_tela = np.full(self.tamanho_janela_pontos, np.nan)
        self.c2_tela = np.full(self.tamanho_janela_pontos, np.nan)
        self.ponteiro_tela = 0  
        
        self.detector_c1 = PanTompkinsRR(self.frequencia_hz)
        self.detector_c2 = PanTompkinsRR(self.frequencia_hz)
        self.trend_tempos = []
        self.trend_bpms = []
        
        self.init_ui()
        
        # Otimização gráfica: atualiza em blocos de 6 amostras (60 FPS)
        self.amostras_por_ciclo = 6  
        intervalo_ms = int((1000 / self.frequencia_hz) * self.amostras_por_ciclo)
        
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.atualizar_sistema)
        self.timer.start(intervalo_ms)

    def init_ui(self):
        self.setWindowTitle("Monitor ECG + detector QRS")
        self.resize(1024, 750)
        
        # Widget e Layout para organizar os três gráficos um em cima do outro
        widget_central = QtWidgets.QWidget()
        self.setCentralWidget(widget_central)
        layout = QtWidgets.QVBoxLayout(widget_central)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        self.plot_c1 = pg.PlotWidget()
        self.plot_c2 = pg.PlotWidget()
        self.plot_trend = pg.PlotWidget()
        
        layout.addWidget(self.plot_c1, stretch=2)
        layout.addWidget(self.plot_c2, stretch=2)
        layout.addWidget(self.plot_trend, stretch=3)
        
        # Configura as curvas e visuais
        self.plot_c1.setBackground('k')
        self.plot_c2.setBackground('k')
        self.plot_c2.setXLink(self.plot_c1)
        
        # Define os limites verticais estáticos de Y baseados na amplitude máxima de cada sinal
        self.plot_c1.setYRange(int(np.min(self.c1_total))-50, int(np.max(self.c1_total))+50)
        self.plot_c2.setYRange(int(np.min(self.c2_total))-50, int(np.max(self.c2_total))+50)
        
        # Define os limites verticais estáticos de Y do trendplot de freq cardíaca
        self.plot_trend.setBackground('#111116')
        self.plot_trend.showGrid(x=True, y=True, alpha=0.3)
        self.plot_trend.setTitle("BPM Instantâneo via Pan-Tompkins (1 / RR)", color='cyan')
        self.plot_trend.setLabel('left', 'FC', units='BPM')
        self.plot_trend.setLabel('bottom', 'Tempo', units='s')
        self.plot_trend.setXRange(0, self.duracao_total_segundos)
        self.plot_trend.setYRange(40, 160)
        
        # Configura as cores e larguras de curva
        pen_c1 = pg.mkPen(color='#00FF00', width=2)   
        pen_c2 = pg.mkPen(color='#FFFF00', width=2)   
        pen_trend = pg.mkPen(color='#00FFFF', width=2) 
        
        # Desenha as curvas iniciais (zeradas por conta dos nan)
        self.curva_c1 = self.plot_c1.plot(self.c1_tela, pen=pen_c1)
        self.curva_c2 = self.plot_c2.plot(self.c2_tela, pen=pen_c2)
        self.curva_trend = self.plot_trend.plot(
            self.trend_tempos, self.trend_bpms, pen=pen_trend, 
            symbol='o', symbolSize=5, symbolBrush='c'
        )
        
        # Executa o ajuste proporcional inicial baseado no tamanho padrão
        self.ajustar_proporcao_janela(self.width())

    # Monitora o redimensionamento da janela
    def resizeEvent(self, event):
        super().resizeEvent(event)
        nova_largura = event.size().width()
        self.ajustar_proporcao_janela(nova_largura)

    # Recalcula o buffer de tela baseado na largura em pixels.
    def ajustar_proporcao_janela(self, largura_pixels):
        # Define um fator multiplicador (Ex: 1.5 pontos de ECG para cada pixel de largura)
        novo_tamanho = int(largura_pixels * 1.5)
        
        # Evita loops ou bugs caso o tamanho seja inválido
        if novo_tamanho == self.tamanho_janela_pontos or novo_tamanho <= 0:
            return
            
        # Cria novos arrays vazios com o tamanho proporcional calculado
        novo_c1_tela = np.full(novo_tamanho, np.nan)
        novo_c2_tela = np.full(novo_tamanho, np.nan)
        
        # Migra os dados antigos que cabem no novo array para não quebrar a animação em execução
        min_tam = min(self.tamanho_janela_pontos, novo_tamanho)
        novo_c1_tela[:min_tam] = self.c1_tela[:min_tam]
        novo_c2_tela[:min_tam] = self.c2_tela[:min_tam]
        
        # Atualiza as referências e reajusta os limites horizontais dos eixos
        self.tamanho_janela_pontos = novo_tamanho
        self.c1_tela = novo_c1_tela
        self.c2_tela = novo_c2_tela
        
        # Se o ponteiro atual ficou fora do novo limite da tela, reinicia ele
        if self.ponteiro_tela >= self.tamanho_janela_pontos:
            self.ponteiro_tela = 0
            
        # Atualiza os limites de exibição do PyQtGraph dinamicamente
        self.plot_c1.setXRange(0, self.tamanho_janela_pontos)

    def atualizar_sistema(self):
        if self.indice_leitura + self.amostras_por_ciclo >= self.total_amostras:
            self.indice_leitura = 0
            self.trend_tempos.clear()
            self.trend_bpms.clear()
            self.detector_c1.contador_amostras = 0
            self.detector_c1.ultimo_pico = 0
            self.detector_c2.contador_amostras = 0
            self.detector_c2.ultimo_pico = 0
            
        novas_amostras_c1 = self.c1_total[self.indice_leitura : self.indice_leitura + self.amostras_por_ciclo]
        novas_amostras_c2 = self.c2_total[self.indice_leitura : self.indice_leitura + self.amostras_por_ciclo]
        
        for i in range(self.amostras_por_ciclo):
            pos_global = self.indice_leitura + i
            tempo_s = pos_global / self.frequencia_hz
            
            if self.ponteiro_tela >= self.tamanho_janela_pontos:
                self.ponteiro_tela = 0
                
            self.c1_tela[self.ponteiro_tela] = novas_amostras_c1[i]
            self.c2_tela[self.ponteiro_tela] = novas_amostras_c2[i]
            self.ponteiro_tela += 1
            
            bpm_c1 = self.detector_c1.processar_amostra(novas_amostras_c1[i])
            bpm_c2 = self.detector_c2.processar_amostra(novas_amostras_c2[i])
            
            bpm_final = bpm_c1 if bpm_c1 is not None else bpm_c2
            if bpm_final is not None:
                self.trend_tempos.append(tempo_s)
                self.trend_bpms.append(bpm_final)
        
        self.indice_leitura += self.amostras_por_ciclo
        
        tamanho_apagamento = 45
        for idx in range(tamanho_apagamento):
            pos_apagamento = (self.ponteiro_tela + idx) % self.tamanho_janela_pontos
            self.c1_tela[pos_apagamento] = np.nan
            self.c2_tela[pos_apagamento] = np.nan
            
        self.curva_c1.setData(self.c1_tela)
        self.curva_c2.setData(self.c2_tela)
        self.curva_trend.setData(self.trend_tempos, self.trend_bpms)

if __name__ == '__main__':
    arquivo_ecg_estereo = "../MIT-BIH-FACIL/sinais/100.wav" 

    app = QtWidgets.QApplication(sys.argv)
    try:
        monitor = MonitorECGCompleto(arquivo_ecg_estereo)
        monitor.show()
        sys.exit(app.exec_())
    except FileNotFoundError:
        print(f"Erro: Arquivo '{arquivo_ecg_estereo}' nao encontrado.")
