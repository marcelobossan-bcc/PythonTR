import numpy as np
from scipy.io import wavfile
import sys
import time

sys.path.append('../')

import detqrs

inicio = time.perf_counter()

nomeArqSaida="resultados_deriv_brev_lote.txt"

# indique aqui se deseja, ou não, excluir o paciente 206 
ignoraPac207=True

pastaSinais="../../MIT-BIH-FACIL/sinais/"
pastaAnotacoes="../../MIT-BIH-FACIL/anotações_mod/"

pacientes = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 111, 112, \
     113, 114, 115, 116, 117, 118, 119, 121, 122, 123, 124, 200, \
     201, 202, 203, 205, 207, 208, 209, 210, 212, 213, 214, 215, \
     217, 219, 220, 221, 222, 223, 228, 230, 231, 232, 233, 234]
    
indBatimentos={1,2,3,4,5,6,7,8,9,10,11,12,13,25,34,35,38}
    
# abre o arquivo texto

arqSaida = open(nomeArqSaida,"w")
arqSaida.write("Paciente\tTP\t\t\t\t\t\tFP\t\t\t\t\tFN\n")

# avalia resultados

limErro=150;    # erro máximo de detecção em ms

tpTotal=0
fnTotal=0
fpTotal=0
npac=0

for i in range(0,48):
    print(pacientes[i])
    if (ignoraPac207==True)and(pacientes[i]==207):
        continue
    else:
        npac+=1
    # lê o sinal
    nomeArq=pastaSinais + str(pacientes[i])+".wav"
    fs,sinal = wavfile.read(nomeArq)
    sinal=(sinal[:,0]-1024)/200
    sinalnp = np.asarray(sinal, dtype=np.float32)
    
    # faz a detecção
    detector = detqrs.DetQRS(sinalnp.size, fs)
    n_qrs,detB = detector.Processa(sinalnp)
    detB=detB[0:np.where(detB<1800*360)[0][-1]]
    
    # lê as anotações
    nomeArq=pastaAnotacoes  + str(pacientes[i])+".ant"
    f=open(nomeArq)
    ref=[]
    for linha in f:
        p=linha.split()
        if int(p[0]) in indBatimentos:
            ref.append(int(p[1]))
    f.close()
    detA=np.array(ref)
    detA=detA[0:np.where(detA<1800*360)[0][-1]]
    
    # calcula parâmetros 
    tp=0
    fn=0;
    nbat=0
    
    for k in detA:
        nbat=nbat+1
        dmin=abs(detB-k).min()
        pos=abs(detB-k).argmin()
        if(dmin/fs<limErro/1000.0):
            tp=tp+1
            detB[pos]=-999999999
        else:
            fn=fn+1
    fp=len(np.extract(detB>0,detB))
    tpTotal+=tp
    fpTotal+=fp
    fnTotal+=fn
    
    # salva os parametros locais
    nomePacTxt="%d: " %(pacientes[i])
    tpTxt="\t\t%d (%2.2f%%)" %(tp,100*tp/nbat)
    fpTxt="\t\t\t%d (%2.2f%%)" %(fp,100*fp/nbat)
    fnTxt="\t\t\t%d (%2.2f%%)" %(fn,100*fn/nbat)
    saidaTxt= nomePacTxt + tpTxt + fpTxt +fnTxt + "\n" 
    arqSaida.write(saidaTxt)
    
# calcula parâmetros globais
totalBatimentos=tpTotal+fnTotal  
Se=100*tpTotal/totalBatimentos
pP=100*tpTotal/(tpTotal+fpTotal)
fD=100*(fpTotal+fnTotal)/totalBatimentos

# salva parametros globais
arqSaida.write("--------------------------------------------------")
arqSaida.write("\n")
totalPacTxt="%d" %(npac)
totalBatTxt="%d" %(totalBatimentos)
tpTotalTxt="%d" %(tpTotal)
fpTotalTxt="%d" %(fpTotal)
fnTotal="%d" %(fnTotal)
SeTxt="%2.2f%%" %(Se)
pPTxt="%2.2f%%" %(pP)
fDTxt="%2.2f%%" %(fD)
if ignoraPac207==True:
    saidaTxt="Total de pacientes: " + totalPacTxt + " (P207 ignorado)"+"\n" 
else:
    saidaTxt="Total de pacientes: " + totalPacTxt + "\n" 
arqSaida.write(saidaTxt)
saidaTxt="Total de batimentos: " + totalBatTxt + "\n" 
arqSaida.write(saidaTxt)
saidaTxt="TP: "+tpTotalTxt + "\tFP: " + fpTotalTxt + "\tFN:"+fnTotal + "\n" 
arqSaida.write(saidaTxt)
saidaTxt="Se: " + SeTxt + "\t+P:" + pPTxt + "\tFD:" + fDTxt + "\n" 
arqSaida.write(saidaTxt)


arqSaida.close()

fim = time.perf_counter()

tempo_total = fim - inicio
print(f"Tempo de execução: {tempo_total:.6f} segundos")


