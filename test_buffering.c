
#include <stdio.h>
#include <windows.h>

void __attribute__((constructor)) flush_init() {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
    printf("DEBUG: Constructor ran\n");
}

int main() {
    int a;
    printf("Nhap a: ");
    // fflush(stdout); // Uncommenting this fixes it manually
    scanf("%d", &a);
    printf("Ban nhap: %d\n", a);
    return 0;
}
