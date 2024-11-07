#include <stdio.h>
#include <stdlib.h>
// Why math? Surely it should be maths - bloody American English
#include <math.h>

unsigned char get8bit(infile)
FILE *infile;
{
   int low;

   low=fgetc(infile);

   return low;
}

int get16bit(infile)
FILE *infile;
{
   int low, high;

   low=fgetc(infile);
   high=fgetc(infile);

   return (high << 8) + low;
}

int main(argc, argv)
int argc;
char **argv;
{
   FILE *infile;
   unsigned int work,morework;
   unsigned int exponent, i, j;
   double mantissa, fp, count;
   int lineno, type;
   int quote=0, token=0;
   char tokens1[255][20]= {
                          "REM",     "DATA",   "",      "",      "READ",  "LIST", "RUN",     "NEW",  "PRINT", "LET",    "FOR",    // 8A
                          "IF",      "THEN",   "GOTO",  "GOSUB", "RETURN","NEXT", "STOP",    "END",  "",      "ON",     "LOAD",   // 95
                          "SAVE",    "VERIFY", "POKE",  "DIM",   "DEF FN","INPUT","RESTORE", "CLR",  "MUSIC", "TEMPO",  "USR(",   // A0
                          "WOPEN",   "ROPEN",  "CLOSE", "MON",   "LIMIT", "CONT", "GET",     "INP#", "OUT#",  "CURSOR", "SET",    // AB
                          "RESET",   "",       "",      "",      "",      "",     "",        "AUTO", "",      "",       "COPY/P", // B6
                          "PAGE/P"
                        };
   char tokens2[255][20] = {
                          "",        "",       "",      "><",    "<>",    "=<",   "<=",      "=>",   ">=",    "",       ">",      // 8A
                          "<",       "",       "",      "",      "",      "",     "",        "",     "",      "",       "",       // 95
                          "",        "",       "",      "",      "",      "",     "",        "",     "TO",    "STEP",   "LEFT$(", // A0
                          "RIGHT$(", "MID$(",  "LEN(",  "CHR$(", "STR$(", "ASC(", "VAL(",    "PEEK(","TAB(",  "SPACE$(","SIZE",   // AB
                          "",        "",       "",      "STRING$(","","CHARACTER$(","CRS",  "CRS", "",      "",       "",         // B6
                          "",        "",       "",      "",      "",      "",     "",        "",     "",      "RND(",   "SIN("    // C1
                          "COS(",    "TAN(",   "ATN(",  "EXP(",  "INT(",  "LOG(",  "LN(",    "ABS(", "SGN(",  "SQR("
                        };
   char sharpascii[255];
   for (i=0;i<256;i++) sharpascii[i]=' ';
   sharpascii[146]='e'; sharpascii[150]='t'; sharpascii[151]='g'; sharpascii[152]='h'; sharpascii[154]='b';
   sharpascii[155]='x'; sharpascii[156]='d'; sharpascii[157]='r'; sharpascii[158]='p'; sharpascii[159]='c';
   sharpascii[160]='q'; sharpascii[161]='a'; sharpascii[162]='z'; sharpascii[163]='w'; sharpascii[164]='s';
   sharpascii[165]='u'; sharpascii[166]='i'; sharpascii[169]='k'; sharpascii[170]='f'; sharpascii[171]='v';
   sharpascii[175]='j'; sharpascii[176]='n'; sharpascii[179]='m'; sharpascii[183]='o'; sharpascii[184]='l';
   sharpascii[189]='y';

   infile=fopen(argv[1],"rb");

   // First check whether it's a BASIC file
   work=get8bit(infile);
   if (work != 0x05 && work != 0x02)
   {
      printf("This isn't an MZ BASIC file\n");
      fclose(infile);
      exit(1);
   }

   // Now skip to the start
   fseek(infile, 0x80, SEEK_SET);

   while (!feof(infile))
   {
      // first get the line length
      work=get16bit(infile);
      if (work == 0x0)
      {
         // End of program
         break;
      }

      // line number
      lineno=get16bit(infile);
      printf("%d ",lineno);
      // First skip the length as we don't care!

      quote=0;
      token=0;
      //Now the rest of the line
      do
      {
         work=get8bit(infile);
         switch (work)
         {
            case 0xd:
               // End of line
               printf("\n");
               break;

            case 0x0b:
            case 0x0c:
               // line number
               if (quote) break;
               morework=get16bit(infile);
               printf("%d", morework);
               break;

            case 0x11:
               // hex integer
               if (quote) break;
               morework=get16bit(infile);
               printf("$%X",morework);
               break;

            case 0x15:
               // FP/integer
               if (quote) break;
               fp=0;
               exponent=get8bit(infile);
               if (exponent & 0x80)
               {
                  exponent-=0x80;
               }
               else if (exponent != 0)
               {
                  exponent=0x80 - exponent;
               }
               //printf("\n%d ",exponent);
               fp=pow(2, (double)exponent);
               //printf(" %g ",fp);
               count=1;
               mantissa=0;
               for (i=0; i<4; i++)
               {
                  morework=get8bit(infile);
                  // This is going to be fun - got through and count each 1 bit
                  for (j=7; j!=0; j--)
                  {
                     if (morework & (1<<j))
                     {
                        //printf("\nHere: %x %g %g %g\n", morework, count, -(count), pow(2, -count));
                        mantissa+=pow(2, -(count));
                     }
                     count++;
                  }
                  //printf("%x ",morework);
               }
               //printf(" %g\n", mantissa);
               mantissa+=pow(2,-1);
               fp*=mantissa;
               if (exponent==0) fp=0;

               printf("%g",fp);
               break;
         }
         if (work >= 0x80 && !quote && !token)
         {
            if (work==0x80)
            {
               work = get8bit(infile);
               printf("%s",tokens1[work-0x80]);
            }
            else
            {
               printf("%s",tokens2[work-0x80]);
            }
            if (work == 0x80)
            {  // Allow lower case in REMs
               token=1;
            }
         }
         else if (work != 0x0)
         {
            // It's a character
            if (work >= 0x80)
            {
               printf("%c", sharpascii[work]);
            }
            else if (work == '\"')
            {
               quote=!quote;
               printf("\"");
            }
            else if (work >= 0x19)  printf("%c",work);
            if (work == 0x3a)
            {
               token=0;
            }
         }
     } while (work != 0x0d);
   }
   fclose(infile);
   exit(0);
}
