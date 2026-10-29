//
// Implementação do método de detecção por derivação e busca reversa
//
// codificado por Marcelo C. Bossan em 08/2021

#include "detqrs_deriv_brev.h"

DetQRS::DetQRS(int dimSinal, int fAmost)
{
//  Construtor da classe DetQRS com algoritmo por derivação e busca reversa
//
//  Se dimSinal >0, o sinal apontado pelo metodo Processa()
//  serah processado em lote, sendo dimSinal o numero de amostras
//	desse sinal.
//
//  Se dimSinal <=0, o sinal serah processado em blocos de amostras,
//  com dimensão retornada pelo metodo RetDimBlocoAmostras(),
//  apresentados sequencialmente ao metodo Processa().
//
//  fAmost eh a frequencia de amostragem do sinal. 
	
	int k;
	int n;
	float atrasoPreProc;
	float tempoBloco = 0.2;
	
	double A150[]={1,-2.531350733982882,2.6156950237100243,-1.3713197168464948,0.3287195965906717};
	double B150[]={0.09976580125861775,0,-0.1995316025172355,0,0.09976580125861775};
	
	double A240[]={1,-3.141740236627907,3.8390421337659895,-2.1851290849137457,0.49543645685221266};
	double B240[]={0.04530532691797782,0,-0.09061065383595564,0,0.04530532691797782};
	
	double A250[]={1,-3.1805503617544506,3.9241162160439633,-2.2464886710640553,0.5094658194636896};
	double B250[]={0.04221355173994535,0,-0.0844271034798907,0,0.04221355173994535};
	
	double A360[]={1,-3.4559150564803285,4.556429509511538,-2.7245823946965704,0.6257367791514479};
	double B360[]={0.02214311385718745,0,-0.0442862277143749,0,0.02214311385718745};
	
	double A500[]={1,-3.6213244230197,4.96338995607754,-3.055047302229134,0.7134582932959054};
	double B500[]={0.012151960625946296,0,-0.024303921251892593,0,0.012151960625946296};
	
	double A720[]={1,-3.744877925414039,5.283244312464704,-3.329231264820996,0.7909812396067903};
	double B720[]={0.006140557589827688,0,-0.012281115179655376,0,0.006140557589827688};
	
	double A1000[]={1,-3.8201718817548884,5.485950188249493,-3.5103996206461434,0.8446535873652864};
	double B1000[]={0.0032822822532476287,0,-0.006564564506495257,0,0.0032822822532476287};
	
	double A1024[]={1,-3.8246206123971622,5.498131971620108,-3.5214843233965802,0.8480023727403623};
	double B1024[]={0.0031360834800954326,0,-0.006564564506495257,0,0.0031360834800954326};
	
	double A2000[]={1,-3.9127333653511664,5.74463869698631,-3.7509532317405085,0.9190500019576345};
	double B2000[]={0.0008544256953335254,0,-0.0017088513906670507,0,0.0008544256953335254};

//	inicializacao de variaveis paramétricas

	fs = fAmost;
	dimBlocoDados = (int)floor((double)tempoBloco * fs);
	dimSinalEntrada=dimSinal;

//	definição dos filtros
	
	freqInvalida=false;
	switch(fs)
	{
		case 150: pre1 = new Filtro(B150, A150, 5,5);
		break;
		
		case 240: pre1 = new Filtro(B240, A240, 5,5);
		break;
		
		case 250: pre1 = new Filtro(B250, A250, 5,5);
		break;
		
		case 360: pre1 = new Filtro(B360, A360, 5,5);
		break;
		
		case 500: pre1 = new Filtro(B500, A500, 5,5);
		break;
		
		case 720: pre1 = new Filtro(B720, A720, 5,5);
		break;
		
		case 1000: pre1 = new Filtro(B1000, A1000, 5,5);
		break;
		
		case 1024: pre1 = new Filtro(B1024, A1024, 5,5);
		break;
		
		case 2000: pre1 = new Filtro(B2000, A2000, 5,5);
		break;
		
		default: freqInvalida=true;
	}

    n=fs/10;
	if(n>10000)
		n=10000;
	double B2[10000]; 
	for(k=0;k<n;k++)
		B2[k]=1.0;
	double A2[1];
	A2[0]=n;
	pre2 = new Filtro(B2, A2, n, 1);					// media movel
	
    atrasoPreProc=0.08;	
    atrasoN=atrasoPreProc*fs;

// inicializacao de variaveis gerais
	
	if (dimSinal > 0)
		numBlocos = (int)ceil(dimSinal / dimBlocoDados);
	else
		numBlocos = 1;
	
	dimVetSinal = dimBlocoDados + 3*fs;
	vetSinal = (float *)malloc(dimVetSinal * sizeof(float));

    pRefratario=0.25*fs;
    largMaxPico=0.3*fs;
    pVerificacao=0.35*fs;
	maxRR=2*fs;
	nPicosDetect=3;
	    
	iniciado=0;
}

DetQRS::~DetQRS()
{
	free(vetSinal);
	delete(pre1);
	delete(pre2);
}

void DetQRS::Inicia(float *sinalPtr, int npts)
{
//	Reinicia o algoritmo
  
	int k;
	
	if(freqInvalida) 
		return;
	
	amostrasLidas = 0;
	
	// faz uma copia do sinal
	
	sinalPtrAux=(float *)malloc(npts*sizeof(float));
	memcpy(sinalPtrAux,sinalPtr,npts*sizeof(float));
	
	// pré-processamento	
	
	pre1->Processa(sinalPtrAux, npts);
	
	for(k=0;k<npts;k++)
		sinalPtrAux[k]=sinalPtrAux[k]*sinalPtrAux[k];
	
	pre2->Processa(sinalPtrAux, npts);
	
	// inicia limiares

    // limiar inicial
    
    limiar=calcDesvPadrao(sinalPtrAux,npts);
    
    // derivada mínima para ser pico

    derivPico=limiar/20;
	
	// reinicia os filtros
	
	pre1->Reset();
	pre2->Reset();	
	
	// inicializa parametros de processamento

    indiceRR=0;
    z1=0;
    z2=0;
    st=1;
    assistolia=0;
    vPico=0;
    vPicoAnt=0;
    posPicoAnt=0;
    picoDetectado=false;
	primeiroQRS=true;
    atLim=3.0/fs;
    buscaReversa=0;
    memo=0;
    memo2=0;
    
	rrMediano=0.8*fs;
	for(k=0;k<8;k++)
		rrMemo[k]=rrMediano;
    
	iniciado=1;
	memset(vetSinal, 0, dimVetSinal * sizeof(float));
	
	free(sinalPtrAux);
}

int DetQRS::RetDimBlocoAmostras()
{
//	Retorna o numero otimo de amostras
	
	if(freqInvalida)
		return 0;

	return dimBlocoDados;
}

int DetQRS::Processa(float *sinalPtr, int *qrs)
{
//  Processamento do algoritmo por derivação e busca reversa
//
//  Se, no construtor, o parametro dimSinal>0, sinalPtr eh
//  um ponteiro para o inicio do sinal a ser processado
//  em lote. Caso contrario, o processamento eh feito em blocos
//  e sinalPtr eh um segmento de nJanela amostras do
//  sinal de ECG, adquirido com resolução de 16 bits 
//  e taxa de amostragem fAmost. Se algum complexo QRS
//  for detectado, o metodo  retorna o numero de deteccoes
//  e o vetor qrs retorna a posicao de cada onda R, dada
//  como o numero de amostras decorridas desde a primeira
//  chamada so objeto ou da ultima chamada do metodo Reinicia().

	bool correcaoQRS;
	int blocos;
	int pos;
	int k;
	int largura;
	int dq;
	float *sPtr;
	float *vetorProc;	
	float *sinal;
	
	if(freqInvalida)
		return 0;
	
	vetorProc = vetSinal + 3*fs;
	sinal=sinalPtr;
	correcaoQRS=false;
    l=0;
	
	// se processando em lote e ainda não fez inicializao de parametros, faz agora

	if((iniciado==0)&&(numBlocos>1))
		Inicia(sinalPtr,2*fs);
	
	// inicio do processamento

	for (blocos = 0; blocos < numBlocos; blocos++, amostrasLidas += dimBlocoDados)
	{
		// le um bloco de dados
	
		if(((dimSinalEntrada-blocos*dimBlocoDados)<dimBlocoDados)&&(numBlocos>1))
			dimBlocoDados=dimSinalEntrada-blocos*dimBlocoDados;

		memmove(vetSinal,vetSinal+dimBlocoDados,(dimVetSinal - dimBlocoDados)*sizeof(float));
		memcpy(vetorProc,sinal+blocos*dimBlocoDados,dimBlocoDados*sizeof(float));

		//	faz pre-processamento

		pre1->Processa(vetorProc, dimBlocoDados);
		
		for (sPtr = vetorProc; sPtr < (vetorProc+dimBlocoDados); sPtr++)
			*sPtr = (*sPtr)*(*sPtr);
		
		pre2->Processa(vetorProc, dimBlocoDados);

		/*****************   INICIO DO ALGORITMO DE DETECCAO   ********************/

		if(amostrasLidas==0)
			sPtr = vetorProc+1;
		else
			sPtr = vetorProc;
		
		while(sPtr < (vetorProc + dimBlocoDados))
		{
			// detecta pico
			
			pos=amostrasLidas+sPtr-vetorProc;

			if((*sPtr-*(sPtr-1))>derivPico)
			{
				z1+=1; 
				z2=0;
				if(z1==1)
					inicioSubida=pos-1;
				if(z1==nPicosDetect)
					st=2;
			}
			else
				z1=0;

			if((*(sPtr-1)-*sPtr)>derivPico)
			{
				z2+=1; 
				z1=0;
				if(z2==1)
					inicioDescida=pos-1;
				if(z2==nPicosDetect)
				{
					if(((inicioDescida-inicioSubida)<largMaxPico)and(st==2))
					{
						largura=pos-inicioSubida;
						for(vPico=0.0,k=0;k<largura;k++)
							if(vPico<*(sPtr-k))
								vPico=*(sPtr-k);
						posPico=inicioSubida; 
						picoDetectado=true;     
					}
					st=1;
				}
			}
			else
				z2=0;  
     
			if(picoDetectado==true)
			{
				// valida pico
					
				if(vPico>limiar)
				{
					if((posPico-posPicoAnt)>pVerificacao)
						qrsValido=true;
					else if((posPico-posPicoAnt)>pRefratario)
					{
						if(vPico>0.25*vPicoAnt)
							qrsValido=true;
						else
							qrsValido=false;	// onda T
					}
					else
					{
						if(vPico>vPicoAnt)
						{
							qrsValido=true;		// correção de posição
							if(l>0)
								l=l-1;
							else
							{
								if((numBlocos==1)&&(primeiroQRS==false))		// processando em blocos isolados
									correcaoQRS=true;
							}
						}
						else
							qrsValido=false;	// dentro do p refratário
					}
					
					// ajusta limiares
					
					limiar=atLim*vPico/8.0+(1-atLim)*limiar;
	
					vPicoAnt=vPico;
					posPicoAnt=posPico;  
					
					// salva QRS
				
					if(qrsValido==true)
					{
						qrs[l]=posPico-atrasoN;
						l+=1;
						assistolia=0;
						if(buscaReversa>0)
						{
							buscaReversa=0;
							derivPico=memo2;
							limiar=memo;
						}
						
						// ajusta intervalo RR
						
						if(primeiroQRS==false)
						{
							dq=qrs[l-1]-qrsAnt;
							if((dq>pVerificacao)&&(dq<maxRR))
							{
								rrMemo[indiceRR]=qrs[l-1]-qrsAnt;
								indiceRR=(indiceRR+1)%8;
								rrMediano=calcMediana(rrMemo,8);
							}
						}
						else
							primeiroQRS=false;
						qrsAnt=qrs[l-1];
					}
				}
				picoDetectado=false;
			}
                
			sPtr++;  
			assistolia+=1;
        
			// busca reversa

			if(assistolia>(rrMediano*1.5))
			{
				buscaReversa+=1;
				if (buscaReversa==1)
				{
					memo=limiar;
					memo2=derivPico;
				}
				
				if(buscaReversa<4)
				{
					limiar*=0.7;
					derivPico*=0.7;
					z1=0;
					z2=0;
					st=1;
					sPtr-=(int)(rrMediano*1.5);
				}
				else
				{
					buscaReversa=0;
					limiar=memo;
					derivPico=memo2;
					sPtr-=largMaxPico;
					z1=0;
					z2=0;
					st=1;
				}
				assistolia=0;
			}
		}
	}	
	
	if(correcaoQRS==true)
		l=-l;
	
	return l;
}

// funções

float DetQRS::calcDesvPadrao(float *vet,int dim)
{	
	float media,desv;
    int i;
	
    for (i=0,media=0;i<dim;i++) 
	{
        media+=vet[i];
    }
    media/=dim;
	
    for (i=0,desv=0;i<dim;i++) 
	{
        desv+=(vet[i]-media)*(vet[i]-media);
    }
    
    return (float)sqrt(desv/dim);
}

int DetQRS::calcMediana(int *vet,int dim)
{	
	int temp;
	int i, j;
	
	for(i=0; i<dim-1; i++) 
		for(j=i+1; j<dim; j++) 
		{
			if(vet[j] < vet[i]) 
			{
				temp = vet[i];
				vet[i] = vet[j];
				vet[j] = temp;
			}
		}
	
	if(dim%2==0) 
		return((vet[dim/2] + vet[dim/2 - 1]) / 2.0);
	else 
		return vet[dim/2];
}
