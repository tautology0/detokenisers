#include <stdio.h>
#include <stdlib.h>

int main(argc, argv)
int argc;
char **argv;
{
   FILE *infile;
   unsigned char work;
   int lineno;
   int quote=0, number=0, length=0;
   char tokens[255][20]={ "AND","DIV","EOR","MOD","OR","ERROR","LINE","OFF","STEP","SPC","TAB(","ELSE",
                          "THEN","line","OPENIN","PTR","PAGE","TIME","LOMEM","HIMEM","ABS","ACS","ADVAL",
                          "ASC","ASN","ATN","BGET","COS","COUNT","DEG","ERL","ERR","EVAL","EXP","EXT",
                          "FALSE","FN","GET","INKEY","INSTR(","INT","LEN","LN","LOG","NOT","OPENUP",
                          "OPENOUT","PI","POINT(","POS","RAD","RND","SGN","SIN","SQR","TAN","TO","TRUE",
                          "USR","VAL","VPOS","CHR$","GET$","INKEY$","LEFT$(","MID$(","RIGHT$(","STR$",
                          "STRING$(","EOF","SUM","WHILE","CASE","WHEN","OF","ENDCASE","OTHERWISE","ENDIF",
                          "ENDWHILE","PTR","PAGE","TIME","LOMEM","HIMEM","SOUND","BPUT","CALL","CHAIN",
                          "CLEAR","CLOSE","CLG","CLS","DATA","DEF","DIM","DRAW","END","ENDPROC","ENVELOPE",
                          "FOR","GOSUB","GOTO","GCOL","IF","INPUT","LET","LOCAL","MODE","MOVE","NEXT","ON",
                          "VDU","PLOT","PRINT","PROC","READ","REM","REPEAT","REPORT","RESTORE","RETURN",
                          "RUN","STOP","COLOUR","TRACE","UNTIL","WIDTH","OSCLI" };

   infile=fopen(argv[1],"rb");
   fseek(infile,0x270,SEEK_SET);
   while (!feof(infile))
   {
		// first get the line length
		work=fgetc(infile);
		if (work == 0)
		{
			// End of program
			break;
		}
		length=work*256+fgetc(infile);
      // first get the line number
      work=fgetc(infile);
      if (work == 0xff)
      {
         // End of program
         break;
      }
      lineno=work*256+fgetc(infile);
      printf("%d ",lineno);
      // First skip the length as we don't care!
      work=fgetc(infile);

      quote=0;
      //Now the rest of the line
      do
      {
         work=fgetc(infile);
         if (work == 0x8d && !quote)
         {
            // It's a line number
            int num1=fgetc(infile), num2=fgetc(infile), num3=fgetc(infile);
            number=num2 - 0x40;
            switch(num1)
            {
               case 0x44: number += 0x40; break;
               case 0x54: break;
               case 0x64: number += 0xc0; break;
               case 0x74: number += 0x80; break;
            }
            number += (num3 - 0x40) * 256;
            printf("%d", number);
         }
         else if (work >= 0x80 && !quote)
         {
            // It's a token!
            printf("%s",tokens[work-0x80]);
         }
         else if (work != 0x0d)
         {
            // It's a character
            printf("%c",work);
            if (work == '\"')
               quote=!quote;
         }
         else
         {
            // End of line
            printf("\n");
         }
      } while (work != 0x0d);
   }
   fclose(infile);
   exit(0);
}
