# 1. projekt do IPK - HTTP resolver doménových jmen
autor: Michal Sova (xsovam00)
## Použití
  - Spuštění serveru
> $ make run PORT=1234
- Příklad užití pomocí příkazu curl
> $ curl localhost:5353/resolve?name=www.seznam.cz\&type=A
## Popis  řešení
Cílem projektu je implementace severu, který komunikuje protokolem HTTP a zajišťuje překlad doménových jmen. Pro překlad jmen server používá resolver metody socket - socket.gethostbyname() a socket.gethostbyaddr() ve funkci resolve(n, t, to_send).
### GET
Operace GET se zpracovává ve funkci get, která vrací zprávu k odeslání klientovi. Ve funkci se kontroluje validnost hlavičky a rozparsovává se URL požadavek. Typ a jméno se posílá do funkce resolve, která (pokud je to možné) provede překlad.
### POST
Operace POST se zpracovává ve funkci post, která vrací příslušnou zprávu k odeslání klientovi. Ve funkci se kontroluje validnost hlavičky a zpracovávají se URL požadavky v těle zprávy. Každý řádek se rozparsovává a zjišťuje se, jestli je validní. Typ a jméno se poté posílá do funkce resolve, která (pokud je to možné) provede překlad. Je-li řádek chybný (špatná doména, chybný formát) řádek se ignoruje.
