#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>

namespace Ui {
class QFGraph;
}

class QFGraph : public QMainWindow
{
    Q_OBJECT

public:
    explicit QFGraph(QWidget *parent = 0);
    ~QFGraph();
    void drawGraph(double a,double b,double c);

private slots:
    void calc();
    void calc1();
    void saveAsIMG();

private:
    Ui::QFGraph *ui;

};



#endif // MAINWINDOW_H
