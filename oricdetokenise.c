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
   char tokens[255][20]={ 
      "END","EDIT","STORE","RECALL","TRON","TROFF","POP","PLOT","PULL","LORES",
      "DOKE","REPEAT","UNTIL","FOR","LLIST","LPRINT","NEXT","DATA","INPUT","DIM","CLS",
      "READ","LET","GOTO","RUN","IF","RESTORE","GOSUB","RETURN","REM","HIMEM","GRAB",
      "RELEASE","TEXT","HIRES","SHOOT","EXPLODE","ZAP","PING","SOUND","MUSIC","PLAY",
      "CURSET","CURMOV","DRAW","CIRCLE","PATTERN","FILL","CHAR","PAPER","INK","STOP","ON",
      "WAIT","CLOAD","CSAVE","DEF","POKE","PRINT","CONT","LIST","CLEAR","GET","CALL","!",
      "NEW","TAB(","TO","FN","SPC(","@","AUTO","ELSE","THEN","NOT","STEP","+","-","*","/",
      "^","AND","OR",">","=","<","SGN","INT","ABS","USR","FRE","POS","HEX$","&","SQR","RND",
      "LN","EXP","COS","SIN","TAN","ATN","PEEK","DEEK","LOG","LEN","STR$","VAL","ASC",
      "CHR$","PI","TRUE","FALSE","KEY$","SCRN","POINT","LEFT$","RIGHT$","MID$"
   };

   infile=fopen(argv[1],"rb");
   fseek(infile,0xd,SEEK_SET);
   // read until the next 00, to get rid of the filename
   do
   {
      work=fgetc(infile);
   } while (work != 0 && !feof(infile));
   
   while (!feof(infile))
   {
		// first get the line length
		work=fgetc(infile);
     // length is the address of the end of the line
		length=work+fgetc(infile)*256;
		if (length == 0)
		{
			// End of program
			break;
		}
       
      // then get the line number
      work=fgetc(infile);
      lineno=work+fgetc(infile)*256;
      
      printf("%d ",lineno);

      quote=0;
      //Now the rest of the line
      do
      {
         work=fgetc(infile);
         /*if (work == 0x8d && !quote)
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
         } */
         if (work >= 0x80 && !quote)
         {
            // It's a token!
            printf("%s",tokens[work-0x80]);
         }
         else if (work != 0x00)
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
      } while (work != 0x00);
   }
   fclose(infile);
   exit(0);
}
