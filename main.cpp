#include "MainWindow.h"
#include <QApplication>
#include <QFileInfo>
#include <QDir>

int main(int argc, char *argv[])
{
    QCoreApplication::addLibraryPath(QFileInfo(QString::fromLocal8Bit(argv[0])).absoluteDir().absoluteFilePath("../PlugIns"));
    QApplication a(argc, argv);
    QFGraph w;
    w.show();
    return a.exec();
}
