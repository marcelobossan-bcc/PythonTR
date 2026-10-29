Arquivos novos/alterados
========================

1. pb.h
   Binding pybind11 da classe DetQRS.

2. detqrs_deriv_brev.h
   Versao do header original com:

       #ifdef DETQRS_ENABLE_PYBIND
       #include "pb.h"
       #endif

   imediatamente depois da declaracao de DetQRS.

3. detqrs_pybind.cpp
   Unidade de compilacao que cria o modulo Python "detqrs".

Compilacao manual no Linux
===========================

Instale pybind11 no ambiente Python usado para executar o modulo:

    python3 -m pip install pybind11

Supondo os arquivos:

    detqrs_pybind.cpp
    detqrs_deriv_brev.cpp
    detqrs_deriv_brev.h
    filtro.cpp
    filtro.h
    pb.h

compile com:

    c++ -O3 -Wall -shared -std=c++17 -fPIC \
        $(python3 -m pybind11 --includes) \
        detqrs_pybind.cpp detqrs_deriv_brev.cpp filtro.cpp \
        -o detqrs$(python3-config --extension-suffix)

Exemplo Python
==============

    import numpy as np
    import detqrs

    fs = 500
    detector = detqrs.DetQRS(0, fs)

    nbloco = detector.RetDimBlocoAmostras()

    # Inicializacao: use um trecho inicial apropriado do ECG.
    inicial = np.asarray(ecg_inicial, dtype=np.float32)
    detector.Inicia(inicial)

    bloco = np.asarray(ecg_bloco, dtype=np.float32)
    n_qrs, posicoes = detector.Processa(bloco)

    print(n_qrs)
    print(posicoes)

Observacao
==========

No codigo C++ original, Processa() pode retornar um valor negativo para
indicar correcao de uma deteccao anterior. O binding preserva esse valor
em n_qrs; o vetor posicoes possui abs(n_qrs) elementos.
