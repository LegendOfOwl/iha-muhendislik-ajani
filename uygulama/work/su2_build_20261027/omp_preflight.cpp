#include <omp.h>
#include <iostream>
int main(){int count=0;
#pragma omp parallel reduction(+:count)
{count+=1;}
std::cout << "{\"threads\":" << count << ",\"openmp_macro\":" << _OPENMP << ",\"double_bytes\":" << sizeof(double) << "}" << std::endl;return count==4 && sizeof(double)==8?0:2;}
