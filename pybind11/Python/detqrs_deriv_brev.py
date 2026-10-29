# detectaQRS(sinal,fs)
# Detector de complexos QRS simples, autoral! :)
#
# entradas:
# sinal: array numpy com sinal de entrada
# fs: taxa de amostragem
# retorna:
# qrs: lista com as amostras correspondentes às ondas R detectadas
# sftr: array numpy com sinal após pré-processamento
# Implementado por Marcelo C. Bossan em 01/2021

import numpy as np
import scipy.signal as sp

def detectaQRS(sinal,fs):
    
    # filtro passa banda com efeito derivativo
    
    fc1=6                   # freq. de corte inferior do filtro passa-baixa
    fc2=25                  # freq. de corte superior do filtro passa-baixa
                            
    w1=2*fc1/fs
    w2=2*fc2/fs
    wp=[w1,w2]
    [B,A]=sp.butter(2,wp,'bp')
    sinalFtr=sp.lfilter(B,A,sinal)**2  # sinal filtrado elev ao quadrado
    
    # filtro média móvel
    
    N=int(fs/10)                    # média móvel 
    A=N
    B=[1]*N
    sinalFtr=sp.lfilter(B,A,sinalFtr)  
    
    atrasoPreProc=0.08
    atrasoN=int(atrasoPreProc*fs)
    
    # inicialização de variáveis do programa
    
    pRefratario=int(0.25*fs)
    largMaxPico=int(0.3*fs)
    pVerificacao=int(0.35*fs)
    rrMediano=0.8*fs
    rrMemo=[rrMediano]*8
    qrs=[0]*20000
    indiceRR=0
    i=1
    z1=0
    z2=0
    st=1
    l=0
    assistolia=0
    nPicosDetect=3
    inicioSubida=0
    inicioDescida=0
    vPico=0
    posPico=0
    vPicoAnt=0
    posPicoAnt=0  
    picoDetectado=False
    atLim=3/fs
    buscaReversa=0
    memo=0
    memo2=0

    # limiar inicial
    
    limiar=sinalFtr[0:2*fs].std()
    
    # derivada mínima para ser pico

    derivPico=limiar/20
    
    # algoritmo principal 

    while i<len(sinalFtr)-1:
        
        # detecta pico positivo

        if sinalFtr[i]-sinalFtr[i-1]>derivPico:
            z1+=1 
            z2=0
            if z1==1:
                inicioSubida=i-1
            if z1==nPicosDetect:
                st=2
        else:
            z1=0

        if sinalFtr[i-1]-sinalFtr[i]>derivPico:
            z2+=1 
            z1=0
            if z2==1:
                inicioDescida=i-1
            if z2==nPicosDetect:
                if (inicioDescida-inicioSubida < largMaxPico) and (st==2):
                    vPico=sinalFtr[inicioSubida:i+1].max()
                    posPico=inicioSubida 
                    picoDetectado=True                    
                st=1
        else:
            z2=0  
     
        if picoDetectado==True:
   
            # valida pico
                
            if vPico>limiar:
                
                if posPico-posPicoAnt>pVerificacao:
                    qrsValido=True
                elif posPico-posPicoAnt>pRefratario:
                    if vPico>0.25*vPicoAnt:
                        qrsValido=True
                    else:
                        qrsValido=False     # onda T
                else:
                    if vPico>vPicoAnt:
                        qrsValido=True
                        if l>0:
                            l=l-1
                    else:
                        qrsValido=False     # dentro do p refratário
                         
                # ajusta limiares
                
                limiar=atLim*vPico/8+(1-atLim)*limiar 
   
                vPicoAnt=vPico
                posPicoAnt=posPico   
                
                # salva QRS
            
                if qrsValido==True:
                    qrs[l]=posPico-atrasoN
                    l+=1  
                    assistolia=0
                    if buscaReversa>0:
                        buscaReversa=0
                        derivPico=memo2
                        limiar=memo
                    
                    # ajusta intervalo RR
                    
                    if l>2:
                        rrMemo[indiceRR]=qrs[l-1]-qrs[l-2]
                        indiceRR=(indiceRR+1)%8
                        rrMediano=np.median(rrMemo)
                
            picoDetectado=False
                
        i+=1   
        assistolia+=1
        
        # # busca reversa
        
        if assistolia > rrMediano*1.5:
            buscaReversa+=1
            if buscaReversa==1:
                memo=limiar
                memo2=derivPico
            if buscaReversa<4:
                limiar*=0.7
                derivPico*=0.7
                z1=0
                z2=0
                st=1
                i-=int(rrMediano*1.5)
            else:
                buscaReversa=0
                limiar=memo
                derivPico=memo2
                i-=largMaxPico
                z1=0
                z2=0
                st=1
            assistolia=0
       
    return qrs[0:l],sinalFtr
