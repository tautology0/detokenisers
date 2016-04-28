#include <stdio.h>
#include <stdlib.h>

#define BASIC_START 0x1c6e
#define BASIC_END 0x1c66

int main(argc, argv)
int argc;
char **argv;
{
   FILE *infile;
   unsigned char work;
   int lineno;
   int quote=0, number=0, length=0;
   int start, end, i;
   char tokens[91][13]=
      {" RND "," INKEY$ "," PI "," FN "," POINT "," SCREEN$ "," ATTR "," AT ",
       " TAB ", " VAL$ "," CODE "," VAL "," LEN "," SIN "," COS "," TAN "," ASN ",
       " ACS ", " ATN "," LN "," EXP "," INT "," SQR "," SGN "," ABS "," PEEK ",
       " IN ", " USR "," STR$ "," CHR$ "," NOT "," BIN "," OR "," AND "," <= ",
       " >= ", " <> "," LINE "," THEN "," TO "," STEP "," DEF FN "," CAT ",
       " FORMAT ", " MOVE "," ERASE "," OPEN # "," CLOSE # "," MERGE "," VERIFY ",
       " BEEP ", " CIRCLE "," INK "," PAPER "," FLASH "," BRIGHT "," INVERSE ",
       " OVER ", " OUT "," LPRINT "," LLIST "," STOP "," READ "," DATA ",
       " RESTORE ", " NEW "," BORDER "," CONTINUE "," DIM "," REM "," FOR ",
       " GO TO ", " GO SUB "," INPUT "," LOAD "," LIST "," LET "," PAUSE ",
       " NEXT "," POKE ", " PRINT "," PLOT "," RUN "," SAVE "," RANDOMIZE ",
       " IF "," CLS "," DRAW ", " CLEAR "," RETURN "," COPYIM "
      };

   infile=fopen(argv[1],"rb");
   // get the start address
   fseek(infile,BASIC_START,SEEK_SET);
   start=fgetc(infile)+(fgetc(infile)*256) - 0x3fe5;
   fseek(infile,BASIC_END,SEEK_SET);
   end=fgetc(infile)+(fgetc(infile)*256) - 0x3fe5;
   printf("%x %x\n",start, end);
   fseek(infile,start,SEEK_SET);
   
   do
   {
      work=fgetc(infile);
      lineno=work*256+fgetc(infile); 
      printf("%d ",lineno);
      
		work=fgetc(infile);
      // length is the address of the end of the line
		length=work+fgetc(infile)*256;
		if (length == 0)
		{
			// End of program
			break;
		}
       
      quote=0;
      //Now the rest of the line
      do
      {

         work=fgetc(infile);
         //printf("Byte: %x\n",work);
         if (work >= 165 && !quote)
         {
            // It's a token!
            printf("%s",tokens[work-165]);
         }
         else if (work==14)
         { /* ignore the number definitions */
            fseek(infile,5,SEEK_CUR);
         }       
         else if (work != 0x0d && work > 0x1f)
         {
            // It's a character
            printf("%c",work);
            if (work == '\"')
               quote=!quote;
         }
         else if (work == 0x0d)
         {
            // End of line
            printf("\n");
         }
      } while (work != 0x0d);
   } while (!feof(infile) && (ftell(infile) < end) && work != 0x80);
   fclose(infile);
   exit(0);
}
