//
// Implementação do método de detecção por derivação e busca reversa
//
// codificado por Marcelo C. Bossan em 08/2021

#ifndef detqrs_h
#define detqrs_h 1

#include <math.h>
#include "filtro.h"

class DetQRS
{
public:
	DetQRS(int dimSinal, int fAmost);
	~DetQRS();
	void Inicia(float *sinalPtr, int npts);
	int RetDimBlocoAmostras();
	int Processa(float *sinalPtr, int *qrs);	
private:
	float calcDesvPadrao(float *vet,int dim);
	int calcMediana(int *vet,int dim);
	bool picoDetectado;
	bool freqInvalida;
	bool qrsValido;
	bool primeiroQRS;
    int pRefratario;
    int largMaxPico;
    int pVerificacao;
	int fs;
	int dimBlocoDados;
	int iniciado;
	int numBlocos;
	int dimVetSinal;
	int atrasoN;
	int amostrasLidas;
	int indiceRR;
	int z1;
	int z2;
	int st;
	int l;
	int assistolia;
	int nPicosDetect;
	int buscaReversa;
	int rrMediano;
	int dimSinalEntrada;
	int qrsAnt;
	int rrMemo[8];
	int inicioSubida;
	int inicioDescida;
	int posPico;
	int posPicoAnt;
	int maxRR;
	float vPico;	
	float vPicoAnt;
	float atLim;	
	float limiar;
	float derivPico;
	float memo;
	float memo2;
	float *vetSinal;	 
	float *sinalPtrAux;
	Filtro *pre1;
	Filtro *pre2;
};

#endif
