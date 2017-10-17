void setAxisLabel(TAxis* a,const char* label) {
  a->SetTitle(label);
  a->SetTitleOffset(1.3);
}

typedef (void*)(TVirtualPad*,TH1*) optFn;
typedef (void*)(TVirtualPad*,TH1*,TH1*&) optFn2;

void noopt(TVirtualPad*,
	   TH1*) {}

void drawH1(TCanvas* c1,
	    int pad, 
	    const char* hname,
	    const char* xlabel,
	    const char* ylabel)
{
  drawH1o(c1,pad,hname,xlabel,ylabel,noopt);
}

void drawH1o(TCanvas* c1,
	     int pad,
	     const char* hname,
	     const char* xlabel,
	     const char* ylabel,
	     void* fn(TVirtualPad*,TH1*))
{
  TH1* h = gROOT->FindObject(hname);
  if (!h) {
    printf("Could not find TH1 %s\n",hname);
    return;
  }
  drawH1o(c1,pad,h,xlabel,ylabel,fn);
}

void drawH1o(TCanvas* c1,
	     int pad, 
	     TH1* h,
	     const char* xlabel,
	     const char* ylabel,
	     void* fn(TVirtualPad*,TH1*))
{
  c1->cd(pad);
  TVirtualPad *c1_2 = c1->Pad();
  c1_2->SetGridx();
  c1_2->SetGridy();
  setAxisLabel(h->GetXaxis(),xlabel);
  setAxisLabel(h->GetYaxis(),ylabel);
  (*fn)(c1_2,h);
  h->Draw();
  c1_2->Modified();
  c1->cd();
}

void drawH1ly(TCanvas* c1,
	      int pad, 
	      const char* hname,
	      const char* xlabel,
	      const char* ylabel)
{
  c1->cd(pad);
  TVirtualPad *c1_2 = c1->Pad();
  c1_2->SetGridx();
  c1_2->SetGridy();
  c1_2->SetLogy();
  TH1* h = gROOT->FindObject(hname);
  setAxisLabel(h->GetXaxis(),xlabel);
  setAxisLabel(h->GetYaxis(),ylabel);
  h->Draw();
  c1_2->Modified();
  c1->cd();
}


void drawH2(TCanvas* c1,
	    int pad, 
	    const char* hname,
	    const char* xlabel,
	    const char* ylabel,
	    const char* zlabel)
{
  drawH2o(c1,pad,hname,xlabel,ylabel,zlabel,noopt);
}

void drawH2o(TCanvas* c1,
	     int pad, 
	     const char* hname,
	     const char* xlabel,
	     const char* ylabel,
	     const char* zlabel,
	     void* fn(TVirtualPad*,TH2*))
{
  TH2* h = gROOT->FindObject(hname);
  drawH2o(c1,pad,h,xlabel,ylabel,zlabel,fn);
}

void drawH2o(TCanvas* c1,
	     int pad, 
	     TH2* h,
	     const char* xlabel,
	     const char* ylabel,
	     const char* zlabel,
	     void* fn(TVirtualPad*,TH2*))
{
  c1->cd(pad);
  TVirtualPad *c1_2 = c1->Pad();
  c1_2->SetGridx();
  c1_2->SetGridy();
  setAxisLabel(h->GetXaxis(),xlabel);
  setAxisLabel(h->GetYaxis(),ylabel);
  setAxisLabel(h->GetZaxis(),zlabel);
  (*fn)(c1_2,h);
  h->Draw("colz");
  c1_2->Modified();
  c1->cd();
}

void drawH2ry(TCanvas* c1,
	      int pad, 
	      const char* hname,
	      const char* xlabel,
	      const char* ylabel,
	      const char* zlabel,
	      float y1,
	      float y2)
{
  c1->cd(pad);
  TVirtualPad *c1_2 = c1->Pad();
  c1_2->SetGridx();
  c1_2->SetGridy();
  TH2F* h = new TH2F(*(TH2F*)gROOT->FindObject(hname));
  setAxisLabel(h->GetXaxis(),xlabel);
  setAxisLabel(h->GetYaxis(),ylabel);
  setAxisLabel(h->GetZaxis(),zlabel);
  h->GetYaxis()->SetRange(y1,y2); 
  h->Draw("colz");
  c1_2->Modified();
  c1->cd();
}

void drawCho(TCanvas* c1,
	     int pad, 
	     TChain* ch,
	     const char* xlabel,
	     const char* ylabel,
	     void* fn(TVirtualPad*,TChain*,TH1*&))
{
  c1->cd(pad);
  TVirtualPad *c1_2 = c1->Pad();
  c1_2->SetGridx();
  c1_2->SetGridy();
  TH1* h;
  (*fn)(c1_2,ch,h);
  setAxisLabel(h->GetXaxis(),xlabel);
  setAxisLabel(h->GetYaxis(),ylabel);
  c1_2->Modified();
  c1->cd();
}

void drawF(TCanvas* c1,
	   int pad,
	   const char* fname,
	   const char* xname,
	   const char* yname,
	   const char* zname)
{
  c1->cd(pad);
  TVirtualPad *c1_2 = c1->Pad();
  c1_2->SetGridx();
  c1_2->SetGridy();
  TF1* h = gROOT->FindObject(fname);
  //  setAxisLabel(h->GetXaxis(),xlabel);
  //  setAxisLabel(h->GetYaxis(),ylabel);
  //  setAxisLabel(h->GetZaxis(),zlabel);
  h->Draw();
  c1_2->Modified();
  c1->cd();
}

void drawFc(TCanvas* c1,
	    int pad,
	    const char* fname,
	    const char* xname,
	    const char* yname,
	    const char* zname)
{
  c1->cd(pad);
  TVirtualPad *c1_2 = c1->Pad();
  c1_2->SetGridx();
  c1_2->SetGridy();
  TF1* h = gROOT->FindObject(fname);
  //  setAxisLabel(h->GetXaxis(),xlabel);
  //  setAxisLabel(h->GetYaxis(),ylabel);
  //  setAxisLabel(h->GetZaxis(),zlabel);
  h->Draw("colz");
  c1_2->Modified();
  c1->cd();
}

void drawDt(TCanvas* c1,
	    int pad,
	    const char* hname,
	    float nturnsperbin)
{
  char buff[80];
  sprintf(buff,"Triggers / Injection / %.1f turns", nturnsperbin);
  drawH1(c1,pad,hname,"Time After Injection (seconds)",buff);
}

TCanvas* createCanvas(const char* title,
		      int nx,
		      int ny,
		      int mode)
{
  TCanvas* c0;
  switch(mode%4) {
  case 0: // landscape
    c0 = new TCanvas(title, title,395,5,800,600);
    break;
  case 1: // portrait
    c0 = new TCanvas(title, title,395,5,600,800);
    break;
  case 2: // square
    c0 = new TCanvas(title, title,395,5,600,600);
    break;
  case 3: // half-square
  default:
    c0 = new TCanvas(title, title,395,5,600,300);
    break;
  }    
  c0->cd();
  TLatex* text = new TLatex(0.4,0.98,title);
  text->SetTextSize(0.02);
  text->Draw();
  if (mode<4)
    c0->Divide(nx,ny,0.01,0.02);
  else
    c0->Divide(nx,ny,0.001,0.001);
  return c0;
}

void Divide(TH2* h2, TH1* h1)
{
  if (h1->GetNbinsX() % h2->GetNbinsX() != 0) {
    printf("Divide: unequally divisible number of bins %d, %d\n",h1->GetNbinsX(),h2->GetNbinsX());
    return;
  }

  unsigned idiv = h1->GetNbinsX() / h2->GetNbinsX();
  printf("Bin ratio is %d\n",idiv);

  unsigned jn=1;
  for(unsigned j=1; j<=h2->GetNbinsX(); j++) {
    double scale = 0.;
    for(unsigned m=0; m<idiv; m++,jn++) {
      scale += h1->GetBinContent(jn);
    }

    if (scale>0) scale = 1./scale;

    for(unsigned k=1; k<=h2->GetNbinsY(); k++) {
      h2->SetBinContent(j,k,h2->GetBinContent(j,k)*scale);
    }
  }
}

TH1D* readHist(istream& s,double errFilter=-1)
{
  char name[32];
  int nbins;
  double xlo,xhi;
  s >> name >> nbins >> xlo >> xhi;
  TH1D* h = new TH1D(name,name,nbins,xlo,xhi);
  char vbuf[32],ebuf[32];
  double ymin=1.e9,ymax=-1.e9;
  for(unsigned j=1; j<=nbins; j++) {
    s >> vbuf >> ebuf;
    if (strcmp(vbuf,"nan") && strcmp(ebuf,"nan")) {
      double v = atof(vbuf);
      double e = atof(ebuf);
      h->SetBinContent(j,v);
      if (e > errFilter) {
	h->SetBinError  (j,e);
	if (v+e > ymax) ymax = v+e;
	if (v-e < ymin) ymin = v-e;
      }
      else {
	h->SetBinError  (j,1.e9);
      }
    }
    else {
      printf("Found %s %s\n",vbuf,ebuf);
      h->SetBinContent(j,0.);
      h->SetBinError  (j,0.);
    }
  }
  h->SetMinimum(ymin-0.1*(ymax-ymin));
  h->SetMaximum(ymax+0.1*(ymax-ymin));
  return h;
}

TH1D* readHist(istream& s,double* xbins,double errFilter=-1)
{
  char name[32];
  int nbins;
  double xlo,xhi;
  s >> name >> nbins >> xlo >> xhi;
  TH1D* h = new TH1D(name,name,nbins,xbins);
  char vbuf[32],ebuf[32];
  double ymin=1.e9,ymax=-1.e9;
  for(unsigned j=1; j<=nbins; j++) {
    s >> vbuf >> ebuf;
    if (strcmp(vbuf,"nan") && strcmp(ebuf,"nan")) {
      double v = atof(vbuf);
      double e = atof(ebuf);
      h->SetBinContent(j,v);
      if (e > errFilter) {
	h->SetBinError  (j,e);
	if (v+e > ymax) ymax = v+e;
	if (v-e < ymin) ymin = v-e;
      }
      else {
	h->SetBinError  (j,1.e9);
      }
    }
    else {
      printf("Found %s %s\n",vbuf,ebuf);
      h->SetBinContent(j,0.);
      h->SetBinError  (j,0.);
    }
  }
  h->SetMinimum(ymin-0.1*(ymax-ymin));
  h->SetMaximum(ymax+0.1*(ymax-ymin));
  return h;
}

double* ffx(double* x,double* p) { return 0; }

TF1* readFunc(ifstream& s)
{
  char name[32];
  double xlo,xhi;
  int npar;
  s >> name >> xlo >> xhi >> npar;
  TF1* f = new TF1(name,ffx,xlo,xhi,npar);
  char pbuf[32],ebuf[32];
  for(unsigned j=0; j<npar; j++) {
    s >> pbuf >> ebuf;
    if (strcmp(pbuf,"nan") && strcmp(ebuf,"nan")) {
      f->SetParameter(j,atof(pbuf));
      f->SetParError (j,atof(ebuf));
    }
    else {
    f->SetParameter(j,0);
    f->SetParError (j,0);
    }
  }
  return f;
}

void dumpHist(ostream& o,TH1D* h)
{
  TAxis* x = h->GetXaxis();
  o << h->GetName() << ' '
    << h->GetNbinsX() << ' '
    << double(x->GetXmin()) << ' '
    << double(x->GetXmax()) << ' ';
  for(unsigned j=1; j<=h->GetNbinsX(); j++) 
    o << double(h->GetBinContent(j)) << ' ' << double(h->GetBinError(j)) << ' ';
  o << endl;
}

void dumpFunc(ostream& o,TF1* f)
{
  TAxis* x = f->GetXaxis();
  o << f->GetName() << ' '
    << double(x->GetXmin()) << ' '
    << double(x->GetXmax()) << ' '
    << f->GetNpar() << ' ';
  for(unsigned j=0; j<f->GetNpar(); j++)
    o << double(f->GetParameter(j)) << ' ' << double(f->GetParError(j)) << ' ';
  o << endl;
}

void dumpArray(ostream& o,double* a,int n)
{
  o << n;
  while(n--)
    o << ' ' << *a++;
  o << endl;
}

double* readArray(istream& s,int& n)
{
  s >> n;
  double* v = new double[n];
  for(unsigned j=0; j<n; j++)
    s >> v[j];
  return v;
}

void getFloat(FILE* f,float* p)
{
  char pbuf[32];
  fscanf(f,"%s",pbuf);
  if (strcmp(pbuf,"nan"))
    *p = atof(pbuf);
  else
    *p = 0;
}

TH1D* array_to_TH1D(const char* name, double* v, int n)
{
  TH1D* h = new TH1D(name,name,n,-0.5,double(n)-0.5);
  for(int k=0; k<n; k++)
    h->SetBinContent(k+1,v[k]);
  return h;
}

TH1D* array_to_TH1D(const char* name, double* v, double* e, int n, int xn=1)
{
  TH1D* h = new TH1D(name,name,n,-0.5,double(n*xn)-0.5);
  for(int k=0; k<n; k++) {
    h->SetBinContent(k+1,v[k]);
    h->SetBinError  (k+1,e[k]);
  }
  return h;
}

TH1D* file_to_TH1D(const char* name, const char* fname, int n)
{
  FILE* f = fopen(fname,"r");
  if (!f) {
    printf("Failed to open %s\n",fname);
    return 0;
  }
  TH1D* h = new TH1D(name,name,n,-0.5,double(n)-0.5);
  int b=1;
  while(!feof(f)) {
    float i, v;
    fscanf(f,"%f %f\n",&i,&v);
    h->SetBinContent(b++,v);
  }
  return h;
}

TH1D* file_to_TH1D_(const char* name, const char* fname, int n)
{
  FILE* f = fopen(fname,"r");
  if (!f) {
    printf("Failed to open %s\n",fname);
    return 0;
  }
  TH1D* h = new TH1D(name,name,n,-0.5,double(n)-0.5);
  int b=1;
  while(!feof(f)) {
    float v;
    fscanf(f,"%f\n",&v);
    h->SetBinContent(b++,v);
  }
  return h;
}

void TTree_stats(TTree* nt, const char* elem,
                 double& mean, double& mean_error)
{
  /*
  double v;
  nt->SetBranchAddress(elem,&v);

  double x=0, xx=0;
  const int n = nt->GetEntries();
  for(int j=0; j<n; j++) {
    nt->GetEntry(j);
    x  += v;
    xx += v*v;
  }
  mean = x/double(n);
  mean_error = sqrt(xx - x*x/double(n))/double(n);

  nt->ResetBranchAddresses();
  */
  nt->Draw(elem);
  mean = nt->GetHistogram()->GetMean();
  mean_error = nt->GetHistogram()->GetMeanError();
}

void nt_GetEntry(TTree* nt, unsigned entry, unsigned offset)
{
  static unsigned npr=1;
  if (entry==0)   npr=1;
  if ((entry%npr)==0) printf("Event %d\n",entry);
  if ((entry%(npr*10))==(npr*10-1)) npr*=10;

  nt->GetEntry(entry+offset);
}

void h_SetMinimums(TH1** array, int n)
{
  double a = array[0]->GetMinimum();
  for(int i=1; i<n; i++)
    a = (array[i]->GetMinimum()<a) ? array[i]->GetMinimum():a;
  for(int i=0; i<n; i++)
    array[i]->SetMinimum(a);
}

void h_SetMaximums(TH1** array, int n)
{
  double a = array[0]->GetMaximum();
  for(int i=1; i<n; i++)
    a = (array[i]->GetMaximum()>a) ? array[i]->GetMaximum():a;
  for(int i=0; i<n; i++)
    array[i]->SetMaximum(a);
}

