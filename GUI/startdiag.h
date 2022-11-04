#ifndef STARTDIAG_H
#define STARTDIAG_H

#include <QDialog>

namespace Ui {
class StartDiag;
}

class StartDiag : public QDialog
{
    Q_OBJECT

public:
    explicit StartDiag(QWidget *parent = 0);
    ~StartDiag();
    void msg(QString msg);

private slots:
    void on_btn_clicked();

private:
    Ui::StartDiag *ui;
};

#endif // STARTDIAG_H
