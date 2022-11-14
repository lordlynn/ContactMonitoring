#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <windows.h>
#include <tchar.h>
#include <stdio.h>
#include <strsafe.h>

namespace Ui {
class MainWindow;
}

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = 0);
    ~MainWindow();

private slots:
    void on_startButton_clicked();

    void on_actionExit_triggered();

    void on_actionOpen_triggered();

    void on_analysisCheckBox_stateChanged(int flag);

    void on_actionSave_triggered();

    void on_isSliding_clicked(bool checked);

    void on_doZones_clicked(bool checked);

    void checkThread(void);

    void on_pushButtonConfig_clicked();

    void on_slidingConfig_clicked();

    void on_stopButton_clicked();

private:
    Ui::MainWindow *ui;
    void ReadFromPipe(CHAR buf[]);
    void ErrorExit(PTSTR lpszFunction);
};

#endif // MAINWINDOW_H
