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
   char tokens[255][20]={ "GOTO", "GOSUB" , "", "RUN", "RETURN", "RESTORE", "RESUME", "LIST", "", "DELETE", "RENUMBER", "AUTO", "", "FOR", "NEXT", "PRINT",
                          "", "INPUT", "", "IF", "DATA", "READ", "DIM", "REM", "END", "STOP", "CONT", "CLS", "", "ON", "LET", "NEW",
                          "POKE", "OFF", "MODE", "SKIP", "PLOT", "LINE", "RLINE", "MOVE", "RMOVE", "TRON", "TROFF", "INP#", "", "GET", "PCOLOR", "PHOME",
                          "HSET", "GPRINT", "KEY", "AXIS", "LOAD", "SAVE", "MERGE", "", "CONSOLE", "", "OUT", "CIRCLE", "TEST", "PAGE", "", "",
                          "ERASE", "ERROR", "", "USR", "BYE", "", "", "DEF", "", "", "", "", "", "", "WOPEN", "CLOSE",
                          "ROPEN", "", "", "", "", "", "", "", "", "KILL", "", "", "", "", "", "",
                          "TO", "STEP", "THEN", "USING", "", "", "TAB", "SPC", "", "", "", "OR", "AND", "", "><", "<>",
                          "=<", "<=", "=>", ">=", "=", ">", "<", "+", "-", "", "", "/", "*", "^","ext1", "ext2"
                        };
   char etokens1[255][64]={ "", "SET", "RESET", "COLOR", "", "", "", "", "", "", "", "", "", "", "", "",
                            "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",
                            "", "", "MUSIC", "TEMPO", "CURSOR", "VERIFY", "CLR", "LIMIT", "", "", "", "", "", "", "BOOT", ""
                          };
   char etokens2[255][64]={ "INT", "ABS", "SIN", "COS", "TAN", "LN", "EXP", "SQR", "RND", "PEEK", "ATN", "SGN", "LOG", "PAI", "", "RAD",
                            "", "", "", "", "", "EOF", "", "", "", "", "", "", "", "", "JOY", "",
                            "", "STR$", "HEX$", "", "", "", "", "", "", "", "", "ASC", "LEN", "VAL", "", "",
                            "", "", "", "ERN", "ERL", "SIZE", "", "", "", "", "LEFT$", "RIGHT$", "MID$", "", "", "",
                            "", "", "", "", "TI$", "", "", "FN"
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
   // Skip the file header
   fseek(infile, 0x80, SEEK_SET);

   // First check whether it's a BASIC file
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
            case 0x0:
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
            if (work == 0xfe)
            { // extended token
               morework=get8bit(infile);
               printf("%s",etokens1[morework-0x80]);
            }
            else if (work == 0xff)
            {
               morework=get8bit(infile);
               printf("%s",etokens2[morework-0x80]);
            }
            else
            {
               printf("%s",tokens[work-0x80]);
            }
            if (work == 0x97 || work == 0x94)
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
     } while (work != 0x00);
   }
   fclose(infile);
   exit(0);
}
