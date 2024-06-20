CC = gcc
LDLIBS = -lm

all: bbcdetokenise c64detokenise cpcdetokenise mz80adetokenise mz80kdetokenise mzdetokenise oricdetokenise specdetokenise

bbcdetokenise: bbcdetokenise.c
	${CC} bbcdetokenise.c -o bbcdetokenise
   
c64detokenise: c64detokenise.c
	${CC} c64detokenise.c -o c64detokenise

cpcdetokenise: cpcdetokenise.c
	${CC} cpcdetokenise.c -o cpcdetokenise
   
mz80adetokenise: mz80adetokenise.c
	${CC} mz80adetokenise.c -o mz80adetokenise ${LDLIBS}

mz80kdetokenise: mz80kdetokenise.c
	${CC} mz80kdetokenise.c -o mz80kdetokenise ${LDLIBS}
   
mzdetokenise: mzdetokenise.c
	${CC} mzdetokenise.c -o mzdetokenise ${LDLIBS}

oricdetokenise: oricdetokenise.c
	${CC} oricdetokenise.c -o oricdetokenise
   
specdetokenise: specdetokenise.c
	${CC} specdetokenise.c -o specdetokenise
   
clean:
	rm *.exe