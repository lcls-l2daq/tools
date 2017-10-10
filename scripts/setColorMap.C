#ifndef setColorMap_C
#define setColorMap_C

void setColorMap() {

  const int nshades = 8;
  const int numcol = 5*nshades;
  static float shades[] = { 0.00, 0.4, 0.5, 0.6,
			    0.7, 0.8, 0.9, 1.0 };

  /*
  const int nshades = 5;
  const int numcol = 5*nshades;
  static float shades[] = { 0.00, 0.4, 0.6,
			    0.8, 1.0 };
  */
  Int_t* colors = new int[numcol];

  float r=1.,g=shades[0],b=shades[0];
  float dc = 1./float(nshades);
  for(unsigned j=0; j<numcol; j++) {
    if (j<nshades)
      g = shades[j];
    else if (j<2*nshades)
      r = shades[2*nshades-j-1];
    else if (j<3*nshades) 
      b = shades[j-2*nshades];
    else if (j<4*nshades)
      g = shades[4*nshades-j-1];
    else
      r = shades[j-4*nshades];
    int icol = j+20;
    if (!gROOT->GetColor(icol)) {
      char name[20];
      sprintf(name,"color%d",icol);
      TColor* color = new TColor(icol,r,g,b,name);
    }
    else {
      TColor* color = gROOT->GetColor(icol);
      color->SetRGB(r,g,b);
    }
    colors[j] = icol;
  }
  gStyle->SetPalette(numcol,colors);
}

#endif
