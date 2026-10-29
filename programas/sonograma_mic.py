############################################################################
#                                                                          #
#       Aulas de REALTIME PYTHON   (PEB/COPPE/UFRJ)                        #
#                                                                          #
#       Exemplo4: Exibição de sonograma de audio lido do microfone         #
#                                                                          #
#       Requer a biblioteca pyqtgraph (cria uma aplicação QtWidgets)       #
#       e a biblioteca sounddevice (para leitura do mic pelo S.O.)         #
#       usando anaconda: conda install -c conda-forge python-sounddevice   #
#                                                                          #
#       Marcelo C Bossan, D.Sc.                                            #
#                                                                          #
#       Outubro/2026                                                       #
#                                                                          #
############################################################################

import sys
import queue

import numpy as np
import sounddevice as sd
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets

# ============================================================
# Configurações
# ============================================================

TAXA_DESEJADA = 44100

TAMANHO_FFT = 1024
NUMERO_FFT_MEDIA = 4

NUMERO_BINS = 511
NUMERO_COLUNAS = 1024

# Faixa de amplitude apresentada no colormap
NIVEL_MIN_DB = -100.0
NIVEL_MAX_DB = 0.0

# Tamanho máximo da fila de blocos recebidos do microfone
TAMANHO_FILA_AUDIO = 100

# ============================================================
# Classe principal
# ============================================================

class Sonograma(QtWidgets.QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("Sonograma")
        self.resize(1200, 700)

        # ----------------------------------------------------
        # Taxa de amostragem
        # ----------------------------------------------------

        self.taxaAmostragem = self.obtemTaxaAmostragem()

        print(
            f"Taxa de amostragem utilizada: "
            f"{self.taxaAmostragem:.1f} amostras/s"
        )

        # ----------------------------------------------------
        # Parâmetros derivados
        # ----------------------------------------------------

        self.resolucaoFrequencia = (self.taxaAmostragem / TAMANHO_FFT)
        self.tempoPorFFT = (TAMANHO_FFT / self.taxaAmostragem)
        self.tempoPorColuna = (NUMERO_FFT_MEDIA *TAMANHO_FFT /self.taxaAmostragem)
        self.tempoTotal = (NUMERO_COLUNAS *self.tempoPorColuna)

        self.frequenciaMaxima = ((NUMERO_BINS - 1) *self.resolucaoFrequencia)

        print(
            f"Resolução espectral: "
            f"{self.resolucaoFrequencia:.3f} Hz/bin"
        )

        print(
            f"Duração de cada FFT: "
            f"{self.tempoPorFFT * 1000:.3f} ms"
        )

        print(
            f"Tempo por coluna: "
            f"{self.tempoPorColuna:.4f} s"
        )

        print(
            f"Tempo total apresentado: "
            f"{self.tempoTotal:.2f} s"
        )

        print(
            f"Frequência máxima apresentada: "
            f"{self.frequenciaMaxima:.1f} Hz"
        )

        # ----------------------------------------------------
        # Fila entre callback de áudio e interface gráfica
        # ----------------------------------------------------
        self.filaAudio = queue.Queue(maxsize=TAMANHO_FILA_AUDIO)

        # ----------------------------------------------------
        # Buffer de áudio
        # ----------------------------------------------------
        self.bufferAudio = np.empty(0,dtype=np.float32)

        # ----------------------------------------------------
        # Janela utilizada nas FFTs
        # ----------------------------------------------------
        self.janelaFFT = np.hanning(TAMANHO_FFT).astype(np.float32)
        self.somaJanela = np.sum(self.janelaFFT)

        # ----------------------------------------------------
        # Acumulação das quatro FFTs
        # ----------------------------------------------------
        self.espectros = []

        # ----------------------------------------------------
        # Matriz do sonograma
        #
        # 511 linhas:
        #     frequência
        #
        # 1024 colunas:
        #     tempo
        # ----------------------------------------------------
        self.dadosSonograma = np.full((NUMERO_BINS,NUMERO_COLUNAS),NIVEL_MIN_DB,dtype=np.float32)

        # ----------------------------------------------------
        # Interface gráfica
        # ----------------------------------------------------
        self.iniciaGraficos()

        # ----------------------------------------------------
        # Inicializa aquisição do microfone
        # ----------------------------------------------------
        self.stream = sd.InputStream(
            samplerate=self.taxaAmostragem,
            channels=1,
            dtype="float32",
            blocksize=TAMANHO_FFT,
            callback=self.callbackAudio
        )
        self.stream.start()

        # ----------------------------------------------------
        # Timer usado apenas para processar dados
        # e atualizar a interface gráfica
        # ----------------------------------------------------

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.processaAudio)
        self.timer.start(20)

    # ========================================================
    # Determina taxa de aquisição
    # ========================================================

    def obtemTaxaAmostragem(self):
        try:
            sd.check_input_settings(channels=1,dtype="float32",samplerate=TAXA_DESEJADA)
            return float(TAXA_DESEJADA)

        except sd.PortAudioError:
            dispositivo = sd.query_devices(kind="input")
            taxa = float(dispositivo["default_samplerate"])
            print("Taxa de 44100 Hz não suportada diretamente.")

            print(
                f"Usando taxa padrão do dispositivo: "
                f"{taxa:.1f} Hz"
            )
            return taxa

    # ========================================================
    # Criação dos gráficos
    # ========================================================

    def iniciaGraficos(self):
        widget = pg.GraphicsLayoutWidget()
        self.setCentralWidget(widget)

        # ----------------------------------------------------
        # Gráfico principal
        # ----------------------------------------------------
        self.grafico = widget.addPlot(title="Sonograma")

        self.grafico.setLabel("left","Frequência",units="Hz")
        self.grafico.setLabel("bottom","Tempo",units="s")

        self.grafico.showGrid( x=True,y=True,alpha=0.25)

        # Evita zoom acidental com o mouse
        self.grafico.setMouseEnabled(x=False,y=False)

        # ----------------------------------------------------
        # Imagem
        # ----------------------------------------------------

        self.imagem = pg.ImageItem(axisOrder="row-major")
        self.grafico.addItem(self.imagem)

        # ----------------------------------------------------
        # Colormap em tons de cinza
        #
        # Preto = baixa amplitude
        # Branco = alta amplitude
        # ----------------------------------------------------

        mapaCinza = pg.ColorMap(
            np.array(
                [
                    0.0,
                    1.0
                ]
            ),
            np.array(
                [
                    [0, 0, 0, 255],
                    [255, 255, 255, 255]
                ],
                dtype=np.uint8
            )
        )

        self.imagem.setColorMap(mapaCinza)
        self.imagem.setLevels([NIVEL_MIN_DB,NIVEL_MAX_DB])
        self.imagem.setImage(self.dadosSonograma,autoLevels=False)

        self.imagem.setRect(
            QtCore.QRectF(-self.tempoTotal,0.0,self.tempoTotal,self.frequenciaMaxima)
        )

        self.grafico.disableAutoRange()

        # ----------------------------------------------------
        # Define explicitamente os limites apresentados
        # ----------------------------------------------------

        self.grafico.setXRange(-self.tempoTotal, 0.0,padding=0)
        self.grafico.setYRange(0.0,self.frequenciaMaxima,padding=0)


    # ========================================================
    # Callback de áudio
    # ========================================================

    def callbackAudio(self,indata,frames,time,status):
        if status:
            print(status,file=sys.stderr)

        dados = indata[:, 0].copy()

        try:
            self.filaAudio.put_nowait(dados)

        except queue.Full:

            try:
                self.filaAudio.get_nowait()
                self.filaAudio.put_nowait(dados)
                print("Perdeu dados")

            except queue.Empty:
                pass

    # ========================================================
    # Processamento dos dados de áudio
    # ========================================================

    def processaAudio(self):
        
        recebeuDados = False

        while True:

            try:

                dados = self.filaAudio.get_nowait()

            except queue.Empty:

                break

            self.bufferAudio = np.concatenate((self.bufferAudio,dados))

            recebeuDados = True

        if not recebeuDados:
            return

        atualizaImagem = False

        # ----------------------------------------------------
        # Processa segmentos consecutivos de 1024 amostras
        # ----------------------------------------------------

        while (self.bufferAudio.size >= TAMANHO_FFT):

            segmento = self.bufferAudio[:TAMANHO_FFT]
            self.bufferAudio = self.bufferAudio[TAMANHO_FFT:]

            # ------------------------------------------------
            # Aplica janela de Hann
            # ------------------------------------------------

            segmentoJanelado = (segmento *self.janelaFFT)

            # ------------------------------------------------
            # Mídulo da FFT real Para 1024 pontos:
            # ------------------------------------------------

            fft = np.fft.rfft(segmentoJanelado,n=TAMANHO_FFT)

            modulo = (2.0 *np.abs(fft) /self.somaJanela)

            # Bin DC não deve receber fator 2
            modulo[0] *= 0.5

            # Usa somente os primeiros 511 bins
            modulo = modulo[:NUMERO_BINS]

            # Guarda o módulo desta FFT
            self.espectros.append(modulo)

            # ------------------------------------------------
            # A cada quatro FFTs
            # ------------------------------------------------

            if (len(self.espectros)== NUMERO_FFT_MEDIA):

                # Média dos módulos das quatro FFTs
                espectroMedio = np.mean(self.espectros,axis=0)
                self.espectros.clear()

                # Converte para decibéis apenas depois
                espectroDb = (20.0 *np.log10(espectroMedio + 1e-12))

                # Limita à faixa do colormap
                espectroDb = np.clip(espectroDb,NIVEL_MIN_DB,NIVEL_MAX_DB)

                # Desloca todo o sonograma uma coluna para a esquerda
                self.dadosSonograma[:, :-1] = (self.dadosSonograma[:, 1:])

                # Insere nova coluna à direita
                self.dadosSonograma[:, -1] = (espectroDb)

                atualizaImagem = True

        # ----------------------------------------------------
        # Atualiza a tela apenas uma vez por chamada
        # ----------------------------------------------------

        if atualizaImagem:
            self.imagem.setImage(self.dadosSonograma,autoLevels=False)

    # ========================================================
    # Fechamento do programa
    # ========================================================

    def closeEvent(self,event):
        self.timer.stop()
        if self.stream.active:
            self.stream.stop()
        self.stream.close()
        event.accept()

# ============================================================
# Programa principal
# ============================================================

if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)

    janela = Sonograma()

    janela.show()

    sys.exit(app.exec())