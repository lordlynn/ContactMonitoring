#include "startdiag.h"
#include "ui_startdiag.h"

StartDiag::StartDiag(QWidget *parent) :
    QDialog(parent),
    ui(new Ui::StartDiag)
{
    ui->setupUi(this);
}

StartDiag::~StartDiag()
{
    delete ui;
}

void StartDiag::msg (QString msg) {
    ui->error_msg->setText(msg.toLocal8Bit().constData());
}

void StartDiag::on_btn_clicked()
{
    StartDiag::close();
}
