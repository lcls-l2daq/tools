#include "rootUtils.C"

static char* p_strtok;

static char* _strtok(char* p)
{
  if (p)
    p_strtok = p;
  else if (p_strtok==NULL)
    return NULL;

  p = p_strtok;

  char* q = strchr(p,' ');
  if (q) {
    *q++=0;
    while(*q == ' ') q++;
    p_strtok = q;
  }
  else 
    p_strtok = NULL;

  return p;
}

void eyescan(const char* fname)
{
  gStyle->SetOptStat(0);
  double xrange = 31.5/64;
  double yrange = 127.7*2.8;

  FILE* f = fopen(fname,"r");
  if (!f) {
    printf("..Done\n");
    break;
  }

  const char* p;
  char* endp;
  char line[4096];
  int linesz=4096;
  double maxSamp=0;

  TH2D* h = new TH2D("BER","BER", 63, -xrange, xrange, 255, -yrange, yrange);

  int nlines=0;
  while(fgets(line,linesz,f)) {
    nlines++;
    p = _strtok(line);
    //    unsigned ix = strtoul(_strtok(line),NULL,0);
    int ix = atoi(p);
    p = _strtok(NULL);
    int iy = atoi(p);
    if (iy < 0) 
      iy = -128-iy;

    p = _strtok(NULL);
    unsigned ie = strtoul(p,&endp,0);
    p = _strtok(NULL);
    double is = strtod(p,&endp);

    double qber = 1.;
    if (is > 0) {
      //   qber = double(ie ? ie:1)/double(is);
      double qe = ie ? double(ie) : 1.;
      double qs = double(is);
      qber = qe/qs;
      // if (qber < 1.e-8)
      //   qber = 0.05*qber;
      // else
        qber = -0.05*log(1-qber);
    }
    
    h->SetBinContent(ix+32, iy+128, qber);

    if (ie==0)
      maxSamp=is;
  }
  
  h->SetMinimum(10**floor(-log10(20*maxSamp)));

  fclose(f);

  if (nlines < 255) { //interpolate missing points
    for(int ix=1; ix<64; ) {
      int mx;
      for(int iy=1; iy<256; ) {
        if (h->GetBinContent(ix,iy)!=0) {
          for(int ny=iy+1; ny<256; ny++)
            if (h->GetBinContent(ix,ny)!=0) break;
          for(nx=ix+1; nx<64; nx++)
            if (h->GetBinContent(nx,iy)!=0) break;
          if (ny<256) {
            printf("Interpolating (%d,%d) to (%d,%d)\n",
                   ix,iy,nx,ny);
            double z0 = h->GetBinContent(ix,iy);
            double z1 = h->GetBinContent(nx,iy);
            double z2 = h->GetBinContent(ix,ny);
            double z3 = h->GetBinContent(nx,ny);
            for(int kx=ix; kx<nx; kx++) {
              // double rx0 = double(kx-ix);
              // double rx1 = double(nx-kx);
              double rx0 = (kx - ix < nx - kx) ? 0 : 1;
              double rx1 = (kx - ix < nx - kx) ? 1 : 0;
              for(int ky=iy; ky<ny; ky++) {
                // double ry0 = double(ky-iy);
                // double ry1 = double(ny-ky);
                double ry0 = (ky - iy < ny - ky) ? 0 : 1;
                double ry1 = (ky - iy < ny - ky) ? 1 : 0;
                double rw = rx0*ry0+rx1*ry0+rx0*ry1+rx1*ry1;
                double z = z0*rx1*ry1 + z1*rx0*ry1 + z2*rx1*ry0 + z3*rx0*ry0;
                z /= rw;
                printf("(%d,%d): (%f,%f,%f,%f): %f\n",
                       kx,ky,z0,z1,z2,z3,z);
                h->SetBinContent(kx,ky,z);
              }
            }
          }
          mx=nx;
          iy=ny;
        }
        else
          iy++;
      }
      ix=mx;
    }
  }

  const char* title = "BER";
  TCanvas* c = createCanvas(fname,1,1,0);

  c->cd(1);
  TVirtualPad *c1_2 = c->Pad();
  c1_2->SetRightMargin(0.14);
  c1_2->SetGridx();
  c1_2->SetGridy();
  c1_2->SetLogz();
  setAxisLabel(h->GetXaxis(),"xoffset, UI");
  setAxisLabel(h->GetYaxis(),"yoffset, mV");
  setAxisLabel(h->GetZaxis(),"BER");
  h->Draw("colz");
  c1_2->Modified();
  c->cd();
}
