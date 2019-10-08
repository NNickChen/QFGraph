#include "MainWindow.h"
#include "ui_MainWindow.h"
#include <QString>
#include <QDebug>
#include <QVector>

QFGraph::QFGraph(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::QFGraph)
{
    ui->setupUi(this);

    QCustomPlot *plot=ui->graph;
    plot->addGraph();
    plot->setInteractions(QCP::iRangeDrag | QCP::iRangeZoom);

    QPen pen;
    pen.setColor(Qt::red);
    pen.setWidth(4);
    plot->graph(0)->setPen(pen);

    plot->xAxis->setLabel("x");
    plot->yAxis->setLabel("y");
    ui->le1->setText("3");
    ui->le2->setText("4");
    ui->le3->setText("5");
    calc();

    connect(ui->le1,SIGNAL(editingFinished()),this,SLOT(calc()));
    connect(ui->le2,SIGNAL(editingFinished()),this,SLOT(calc()));
    connect(ui->le3,SIGNAL(editingFinished()),this,SLOT(calc()));
    connect(ui->le4,SIGNAL(editingFinished()),this,SLOT(calc1()));
    connect(ui->le5,SIGNAL(editingFinished()),this,SLOT(calc1()));
    connect(ui->le6,SIGNAL(editingFinished()),this,SLOT(calc1()));
    connect(ui->acSaveAsIMG,SIGNAL(triggered()),this,SLOT(saveAsIMG()));
}

QFGraph::~QFGraph()
{
    delete ui;
}

void QFGraph::calc()
{
    QString str1,str2,str3;
    str1=ui->le1->text();
    str2=ui->le2->text();
    str3=ui->le3->text();
    if(str1.size()<=0||str2.size()<=0||str3.size()<=0)
    return;
    double a,b,c;
    a=str1.toDouble();
    b=str2.toDouble();
    c=str3.toDouble();
    ui->le4->setText(QString::number(a));
    ui->le5->setText(QString::number(b/(2*a)));
    ui->le6->setText(QString::number((4*a*c-b*b)/(4*a)));
    drawGraph(a,b,c);
    return;
}

void QFGraph::calc1()
{
    QString str1,str2,str3;
    str1=ui->le4->text();
    str2=ui->le5->text();
    str3=ui->le6->text();
    if(str1.size()<=0||str2.size()<=0||str3.size()<=0)
    return;
    double a,b,c;
    a=str1.toDouble();
    b=str2.toDouble();
    c=str3.toDouble();
    ui->le1->setText(QString::number(a));
    ui->le2->setText(QString::number(2*a*b));
    ui->le3->setText(QString::number(a*b*b+c));
    drawGraph(a,2*a*b,a*b*b+c);
    return;
}

void QFGraph::drawGraph(double a,double b,double c)
{
    QCustomPlot *plot=ui->graph;
    QVector<double> x,y;
    if(a==0) return;
    double vertexX=-b/(2*a);
    double vertexY=(4*a*c-b*b)/(4*a);
    for(double i=vertexX-10000;i<=vertexX+10000;i+=0.01)
    {
        x.append(i);
        y.append(a*i*i+b*i+c);
    }
    plot->graph(0)->setData(x,y);
    plot->xAxis->setRange(vertexX-2.5,vertexX+2.5);
    if(a>0)
    plot->yAxis->setRange(vertexY-0.5,vertexY+4.5);
    else
    plot->yAxis->setRange(vertexY-4.5,vertexY+0.5);
    plot->replot();
    return;
}

void QFGraph::saveAsIMG()
{
    qDebug()<<"saveAsIMG is running!\n";
    QString fileName=QFileDialog::getSaveFileName(this,tr(""),"",tr("Img(*.jpg)")); //选择路径
    if(fileName.size()<=0) return;
    ui->graph->saveJpg(fileName);
}
