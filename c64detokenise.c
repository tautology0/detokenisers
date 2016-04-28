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
   int offset;
   int basicstart;
   unsigned char workspace[255];
   int end=0;
   
   char tokens[255][20]={ 
      "END","FOR","NEXT","DATA","INPUT#","INPUT","DIM","READ","LET",
      "GOTO","RUN","IF","RESTORE","GOSUB","RETURN","REM","STOP","ON",
      "WAIT","LOAD","SAVE","VERIFY","DEF","POKE","PRINT#","PRINT",
      "CONT","LIST","CLR","CMD","SYS","OPEN","CLOSE","GET","NEW",
      "TAB(","TO","FN","SPC(","THEN","NOT","STEP","+","-","*","/",
      "^","AND","OR",">","=","<","SGN","INT","ABS","USR","FRE","POS",
      "SQR","RND","LOG","EXP","COS","SIN","TAN","ATN","PEEK","LEN",
      "STR$","VAL","ASC","CHR$","LEFT$","RIGHT$","MID$","GO"
   };

   infile=fopen(argv[1],"rb");
   fseek(infile,0x66,SEEK_SET);
   // Check that we're at C64MEM
   fread(workspace, 1, 0xf, infile);
   if (strcmp(workspace,"C64MEM")!=0)
   {
      printf("Could not find C64MEM chunk, exiting\n");
      exit(1);
   }
   // Otherwise, offset is set:
   offset=0x80;
   fseek(infile, 0x2b + offset,SEEK_SET);
   basicstart=fgetc(infile)+fgetc(infile)*256;
   printf("start: %x\n", basicstart);
  
   fseek(infile, basicstart+offset, SEEK_SET);
   do
   {
      // length is the address of the end of the line
		length=fgetc(infile)+fgetc(infile)*256;
      if (length == 0)
      {
         end=1;
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
   } while (!end);
   fclose(infile);
   exit(0);
}
