#ifndef filtro_h
#define filtro_h 1

#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include<float.h>

class Filtro
{
public:
  Filtro(double *B,double *A,int nb,int na);
  ~Filtro();
  void Processa(float *sinal, int dim);
  void Reset();
private:
  int dimA;
  int dimB;
  double *coefA;
  double *coefB;
  float *memoX;
  double *memoY;
};

#endif