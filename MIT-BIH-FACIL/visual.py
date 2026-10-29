# -*- coding: utf-8 -*-
# Gera interface gráfica para visualização de um canal de sinal
#
# O paciente é selecionado alterando o índice da variável paciente, na
# linha 40 do programa. A próxima linha indica a localização
# relativa da base MIT-BIH-FACIL
# 
# Implementado por Marcelo C. Bossan em 03/2021

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox
from matplotlib.widgets import Button
from scipy.io import wavfile
import sys

paciente=105
pastaMBF='../'

sys.path.append('../')

# função para a plotagem dos gráficos

def plota(ax,grf,fs,inicio,tamanho,ref,nome):
    # plota o grafico do sinal
    # se det=True, deixa espaço para exibição de detecção
    
    xmin=inicio/fs
    xmax=(inicio+tamanho)/fs
    ymin=grf[inicio:inicio+tamanho].min()
    ymax=grf[inicio:inicio+tamanho].max()
    
    auxNome=[]
    auxPos=[] 

    spc=(ymax-ymin)*0.05
    ymax+=spc
    for i in range(0,len(ref)):
        if (ref[i][0]>=inicio)and(ref[i][0]<inicio+tamanho):
            auxPos.append(ref[i][0])  
            auxNome.append(ref[i][1])     
        
    # plota sinal
        
    ax.clear()
    ax.set_title(nome,fontdict={'weight': 'bold', 'size': 12},color = 'darkblue')
    ax.axis([xmin,xmax,ymin,ymax])
    ax.plot(np.arange(inicio,inicio+tamanho)/fs,grf[inicio:inicio+tamanho],
            'darkblue')

    # plota classes
    
    for i in range(0,len(auxNome)):
        ax.text(auxPos[i]/fs,ymax-spc,auxNome[i],
                      fontdict={'weight': 'bold', 'size': 6},color = 'red')    
        
# ----------------------------------------------------------------
#                      PROGRAMA PRINCIPAL
# ----------------------------------------------------------------

# le o sinal

txt=pastaMBF+'MIT-BIH-FACIL/sinais/%d.wav' %(paciente)
fs,data = wavfile.read(txt)
data=(data-1024)/200

# le o arquivo de anotações e exclui todo símbolo não-QRS

indBatimentos={1,2,3,4,5,6,7,8,9,10,11,12,13,25,34,35,38}
tipo={1:"N",2:"LB",3:"RB",4:"AB",5:"PVC",6:"FUS",
       7:"NPC",8:"APC",9:"SVPB",10:"VESC",11:"NESC",12:"PACE",
       13:"U",25:"BBB",34:"AESC",35:"SVE",38:"PFUS"}

txt=pastaMBF+'MIT-BIH-FACIL/anotações_mod/%d.ant' %(paciente)
f=open(txt)
ref=[]
for linha in f:
    p=linha.split()
    if int(p[0]) in indBatimentos:
        ind0=int(p[0])
        ind1=int(p[1])
        batim=[ind1,tipo[ind0]]
        ref.append(batim)

# desenha a interface gráfica

plt.close()
my_dpi=100
plt.figure("Visualização dos canais",figsize=(1600/my_dpi, 800/my_dpi), dpi=my_dpi)

# gráficos
plt.subplots_adjust(hspace=0.25)
axGrf1=plt.subplot(2,1,1)
axGrf2=plt.subplot(2,1,2,sharex=axGrf1)

class Index(object):
    p = 0
    def retornaTela1(self, event):
        if self.p>=20:
            self.p-=20
        else:
            self.p=0
        plota(axGrf1,data[:,0],fs,self.p*fs,20*fs,ref,'Canal1') 
        plota(axGrf2,data[:,1],fs,self.p*fs,20*fs,ref,'Canal1') 
        plt.draw()
        
    def retornaTela2(self, event):
        if self.p>=60:
            self.p-=60
        else:
            self.p=0
        plota(axGrf1,data[:,0],fs,self.p*fs,20*fs,ref,'Canal1') 
        plota(axGrf2,data[:,1],fs,self.p*fs,20*fs,ref,'Canal2') 
        plt.draw()
        
    def avancaTela1(self, event):
        if self.p+20<len(data[:,0]):
            self.p+=20
        plota(axGrf1,data[:,0],fs,self.p*fs,20*fs,ref,'Canal1') 
        plota(axGrf2,data[:,1],fs,self.p*fs,20*fs,ref,'Canal2') 
        plt.draw()
        
    def avancaTela2(self, event):
        if self.p+60<len(data[:,0]):
            self.p+=60
        plota(axGrf1,data[:,0],fs,self.p*fs,20*fs,ref,'Canal1') 
        plota(axGrf2,data[:,1],fs,self.p*fs,20*fs,ref,'Canal2') 
        plt.draw()
 
# botões
callback = Index()
axRetorna1 = plt.axes([0.44, 0.47, 0.04, 0.035])
axAvança1 = plt.axes([0.55, 0.47, 0.04, 0.035])
btRetorna1= Button(axRetorna1, '<- 20s')
btRetorna1.on_clicked(callback.retornaTela1)
btAvança1 = Button(axAvança1, '20s ->')
btAvança1.on_clicked(callback.avancaTela1)
axRetorna2 = plt.axes([0.39, 0.47, 0.04, 0.035])
axAvança2 = plt.axes([0.60, 0.47, 0.04, 0.035])
btRetorna2= Button(axRetorna2, '<- 60s')
btRetorna2.on_clicked(callback.retornaTela2)
btAvança2 = Button(axAvança2, '60s ->')
btAvança2.on_clicked(callback.avancaTela2)

# janelas de texto
axPac = plt.axes([0.20, 0.47, 0.04, 0.035])
janPac=TextBox(axPac,'Paciente:',initial=str(paciente))
   
#desenho dos gráficos

plota(axGrf1,data[:,0],fs,0,20*fs,ref,'Canal1') 
plota(axGrf2,data[:,1],fs,0,20*fs,ref,'Canal2')

plt.show()       

    

    
