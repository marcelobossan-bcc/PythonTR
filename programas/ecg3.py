############################################################################
#                                                                          #
#       Aulas de REALTIME PYTHON   (PEB/COPPE/UFRJ)                        #
#                                                                          #
#       Exemplo4: Exibição de ECG em tempo real + det QRS  (ecg3.py)       #
#       usa o MIT-BIH-FACIL (mod do MIT-BIH distribuído pela Physinet      #
#                                                                          #
#       Requer a biblioteca pyqtgraph (cria uma aplicação QtWidgets)       #
#       e o modulo nativo detqrs (.so)                                     #
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
from pathlib import Path
import detqrs

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

class DetectorQRSNativo:
    def __init__(self, fs, sinal_inicial):
        self.fs = fs
        self.detector = detqrs.DetQRS(-1, fs)  # -1: processamento em blocos
        self.tamanho_bloco = self.detector.RetDimBlocoAmostras()
        if self.tamanho_bloco <= 0:
            raise ValueError(f"Frequencia de amostragem nao suportada: {fs} Hz")

        # Inicia os limiares com dois segundos do proprio sinal, como na
        # aplicacao C++ de avaliacao. Processa() depois comeca na amostra zero.
        inicio = np.ascontiguousarray(sinal_inicial[:2 * fs], dtype=np.float32)
        if inicio.size < 2 * fs:
            raise ValueError("O arquivo ECG precisa ter pelo menos 2 segundos")
        self.detector.Inicia(inicio)
        self.posicoes_qrs = []

    def processar_bloco(self, bloco):
        dados = np.ascontiguousarray(bloco, dtype=np.float32)
        if dados.size != self.tamanho_bloco:
            raise ValueError("O bloco de ECG tem tamanho diferente do esperado pelo detector")

        # Retorno: (numero_de_deteccoes, array_de_posicoes_absolutas).
        # Numero negativo indica correcao de uma deteccao do bloco anterior.
        n_qrs, posicoes = self.detector.Processa(dados)
        if n_qrs < 0 and self.posicoes_qrs:
            self.posicoes_qrs.pop()

        if n_qrs != 0:
            novos = np.asarray(posicoes).ravel()[:abs(n_qrs)]
            self.posicoes_qrs.extend(int(pos) for pos in novos if pos >= 0)
        return n_qrs != 0

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
        
        # Dados exibidos na escala original do WAV; dados do detector em mV,
        self.sinal_c1_mv = np.ascontiguousarray(
            (self.c1_total.astype(np.float32) - 1024.0) / 200.0
        )
        self.sinal_c2_mv = np.ascontiguousarray(
            (self.c2_total.astype(np.float32) - 1024.0) / 200.0
        )
        self.criar_detectores()
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
        self.plot_trend.setTitle("BPM instantaneo via detector QRS nativo (1 / RR)", color='cyan')
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

    def criar_detectores(self):
        # Cria uma instancia independente da biblioteca para cada canal.
        self.detector_c1 = DetectorQRSNativo(self.frequencia_hz, self.sinal_c1_mv)
        self.detector_c2 = DetectorQRSNativo(self.frequencia_hz, self.sinal_c2_mv)
        self.tamanho_bloco_qrs = self.detector_c1.tamanho_bloco
        if self.detector_c2.tamanho_bloco != self.tamanho_bloco_qrs:
            raise RuntimeError("Os detectores retornaram tamanhos de bloco diferentes")
        self.inicio_proximo_bloco = 0

    def reiniciar_reproducao(self):
        self.indice_leitura = 0
        self.ponteiro_tela = 0
        self.c1_tela.fill(np.nan)
        self.c2_tela.fill(np.nan)
        self.trend_tempos.clear()
        self.trend_bpms.clear()
        # O .so nao expoe um reset completo; recriar os objetos tambem
        # reinicia filtros, limiares, posicao das amostras e estado de busca.
        self.criar_detectores()

    def atualizar_frequencia_cardiaca(self):
        # Combina deteccoes dos canais, eliminando duplicatas a ate 100 ms.
        # Se os dois canais detectarem o mesmo batimento, prefere o canal 1.
        eventos = ([(pos, 0) for pos in self.detector_c1.posicoes_qrs] +
                   [(pos, 1) for pos in self.detector_c2.posicoes_qrs])
        eventos.sort()
        janela_duplicata = int(0.100 * self.frequencia_hz)
        batimentos = []
        for pos, canal in eventos:
            if batimentos and pos - batimentos[-1][0] <= janela_duplicata:
                if canal < batimentos[-1][1]:
                    batimentos[-1] = (pos, canal)
            else:
                batimentos.append((pos, canal))

        self.trend_tempos.clear()
        self.trend_bpms.clear()
        for anterior, atual in zip(batimentos, batimentos[1:]):
            intervalo_rr = atual[0] - anterior[0]
            if intervalo_rr <= 0:
                continue
            bpm = 60.0 * self.frequencia_hz / intervalo_rr
            if 40 <= bpm <= 160:
                self.trend_tempos.append(atual[0] / self.frequencia_hz)
                self.trend_bpms.append(bpm)

    def atualizar_sistema(self):
        if self.indice_leitura + self.amostras_por_ciclo > self.total_amostras:
            self.reiniciar_reproducao()

        fim = self.indice_leitura + self.amostras_por_ciclo
        novas_amostras_c1 = self.c1_total[self.indice_leitura:fim]
        novas_amostras_c2 = self.c2_total[self.indice_leitura:fim]

        # Mantem a animacao de 6 amostras/ciclo, independente do bloco nativo.
        for a1, a2 in zip(novas_amostras_c1, novas_amostras_c2):
            if self.ponteiro_tela >= self.tamanho_janela_pontos:
                self.ponteiro_tela = 0
            self.c1_tela[self.ponteiro_tela] = a1
            self.c2_tela[self.ponteiro_tela] = a2
            self.ponteiro_tela += 1

        self.indice_leitura = fim

        # O detector C++ recebe blocos completos (72 amostras a 360 Hz).
        # Ao preencher um bloco, envia-o para ambos os canais.
        mudou_qrs = False
        while self.inicio_proximo_bloco + self.tamanho_bloco_qrs <= fim:
            inicio = self.inicio_proximo_bloco
            final = inicio + self.tamanho_bloco_qrs
            mudou_c1 = self.detector_c1.processar_bloco(self.sinal_c1_mv[inicio:final])
            mudou_c2 = self.detector_c2.processar_bloco(self.sinal_c2_mv[inicio:final])
            mudou_qrs = mudou_qrs or mudou_c1 or mudou_c2
            self.inicio_proximo_bloco = final

        if mudou_qrs:
            self.atualizar_frequencia_cardiaca()

        tamanho_apagamento = 45
        for idx in range(tamanho_apagamento):
            pos_apagamento = (self.ponteiro_tela + idx) % self.tamanho_janela_pontos
            self.c1_tela[pos_apagamento] = np.nan
            self.c2_tela[pos_apagamento] = np.nan

        self.curva_c1.setData(self.c1_tela)
        self.curva_c2.setData(self.c2_tela)
        if mudou_qrs:
            self.curva_trend.setData(self.trend_tempos, self.trend_bpms)

if __name__ == '__main__':
    arquivo_ecg_estereo = str(
        Path(__file__).resolve().parent.parent / "MIT-BIH-FACIL" / "sinais" / "100.wav"
    )

    app = QtWidgets.QApplication(sys.argv)
    try:
        monitor = MonitorECGCompleto(arquivo_ecg_estereo)
        monitor.show()
        sys.exit(app.exec() if hasattr(app, 'exec') else app.exec_())
    except FileNotFoundError:
        print(f"Erro: Arquivo '{arquivo_ecg_estereo}' nao encontrado.")
