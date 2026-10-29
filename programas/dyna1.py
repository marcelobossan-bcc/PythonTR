############################################################################
#                                                                          #
#       Aulas de REALTIME PYTHON   (PEB/COPPE/UFRJ)                        #
#                                                                          #
#       Exemplo1: Exibição de gráfico dinâmico em python  (dyna1.py)       #
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

# 1. Cria a aplicação Qt
app = QtWidgets.QApplication([])

# 2. Cria a janela do gráfico
win = pg.plot(title="Gráfico Dinâmico em Tempo Real")
win.resize(800, 400)
win.showGrid(x=True, y=True)
win.setLabel('bottom', 'Tempo (s)')

# 3. Configura a curva e os dados iniciais
dados = np.random.normal(size=100)
curva = win.plot(dados, pen=pg.mkPen('g', width=2)) # Linha verde com espessura 2

# 4. Função de atualização dos dados
def atualizar():
    global dados
    # Remove o primeiro elemento e adiciona um novo valor aleatório no final
    dados[:-1] = dados[1:]
    dados[-1] = np.random.normal()
    
    # Atualiza o gráfico com os novos dados
    curva.setData(dados)

# 5. Configura o Timer para rodar a função a cada 50 milissegundos
timer = QtCore.QTimer()
timer.timeout.connect(atualizar)
timer.start(20) 

# Executa a aplicação
app.exec_()
