function QRS = filtraqrs(A)
%QRS = filtraqrs(A)
%filtra uma matriz de anotações deixando apenas as anotações 
%correspondentes a complexos QRS
%A matriz A deve possuir duas colunas, onde cada linha deve ser da forma
%[índice numAmostra]

i=((A(:,1)<14)&(A(:,1)>0))|(A(:,1)==25)|(A(:,1)==34)|(A(:,1)==35)|(A(:,1)==38 |(A(:,1)==31));

QRS=A(i,:);
end

