#include "filtro.h"

Filtro::Filtro(double *B, double *A, int nb, int na)
{
//	Construtor do Filtro, onde B eh o vetor de coeficientes, com nb elementos, que
//	multiplicam o sinal de entrada x(n), A eh o vetor de coeficientes, com nb 
//  elementos, que multiplicam o sinal de saída y(n), segundo a equação
//
//	    a(0)*y(n) = b(0)*x(n) + b(1)*x(n-1) + ... + b(nb-1)*x(n-nb-1)
//		-a(1)*y(n - 1) - ... - a(na-1)*y(n - na-1)
  
	int cont;

	dimA=na;
	dimB=nb;
	coefA=(double *)malloc(na*sizeof(double));
	coefB=(double *)malloc(nb*sizeof(double));
	memcpy(coefA,A,na*sizeof(double));
	memcpy(coefB,B,nb*sizeof(double));
	
	memoX=(float *)malloc(dimB*sizeof(float));	
	memoY=(double *)malloc(dimA*sizeof(double));
	
	Reset();
	
	// para evitar interrupcoes por 0x0
	
	for(cont=0;cont<na;cont++)	
		if(coefA[cont]==0)
			coefA[cont]=FLT_MIN;
		
	for(cont=0;cont<nb;cont++)
		if(coefB[cont]==0)
			coefB[cont]=FLT_MIN;
}

Filtro::~Filtro()
{
	free(coefA);
	free(coefB);
	free(memoX);
	free(memoY);
}

void Filtro::Reset()
{
	// zera as memorias dos filtros
  
	memset(memoX,0,dimB*sizeof(float));
	memset(memoY,0,dimA*sizeof(double));	
}

void Filtro::Processa(float *sinal, int dim)
{
//  Filtra sinal de dimensao dim

	double *coef,*memo;
	double y;
	float *sFtr,*memof;

	for(sFtr=sinal;sFtr<sinal+dim;sFtr++)
	{
		memmove(&memoX[1],memoX,(dimB-1)*sizeof(float));
		memoX[0]=*sFtr;

		for (y=0,coef=coefB,memof=memoX;coef<coefB+dimB;coef++,memof++)
			y+=(*coef)*(*memof);

		if(dimA>1)
		{
			for (coef=&coefA[1],memo=memoY;coef<coefA+dimA;coef++,memo++)
				y-=(*coef)*(*memo);
			memmove(&memoY[1],memoY,(dimA-1)*sizeof(double));
		}
		y/=coefA[0];

		memoY[0]=y;
		*sFtr=(float)y;
	}
}
