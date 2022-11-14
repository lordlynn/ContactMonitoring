#include "mainwindow.h"
#include "ui_mainwindow.h"
#include <iostream>
#include "qfiledialog.h"

#include <thread>
#include <future>
#include <QTimer>

//#include "windows.h"
//#include "tchar.h"

#include "startdiag.h"
#include <fstream>


bool processFlag = false;
PROCESS_INFORMATION pi;


// Flags and Strings for setting up command to run
QStringList files;
QString save_dir;
bool analysis_flag = false;
bool sliding_flag = false;
bool zone_flag = false;

// Use these flags to check if all required infiormtion has been entered by the user before calling py script
bool checkOpen = false;
bool checkSave = false;

// Used to calculate progress bar. stores total number of files to convert
int pn = 0;

// Signal to kill active process
bool stop_flag = false;



MainWindow::MainWindow(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::MainWindow)
{
    freopen("out.txt", "a", stdout);

    // Calls the checkThread slot periodically
    QTimer *timer = new QTimer(this);
    connect(timer, &QTimer::timeout, this, MainWindow::checkThread);
    timer->start(1000);

    ui->setupUi(this);
}

MainWindow::~MainWindow()
{
    if (processFlag) {
        std::string cmd = "taskkill /pid " + std::to_string(pi.dwProcessId) + " /t /f";
        const char *charCmd = cmd.c_str();
        WinExec(charCmd, SW_HIDE);
    }
    delete ui;
    fclose(stdout);
}


void MainWindow::checkThread()
{
    float status = 0.0;
    static int last = 0.0;

    if (processFlag) {
        try {
            std::string line;
            std::ifstream fp("status.txt");
            if (fp.is_open()) {
                while (std::getline(fp, line)) {
                    for (int i = 0; i < pn; i++) {
                        if ((0.1 * (float)(line[i*3] - '0') + 0.01 * (float)(line[i*3 + 1] - '0')) >= 0.99)
                            status += (1/ (float)pn);
                        else
                            status += (1 / (float)pn) * (0.1 * (float)(line[i*3] - '0') + 0.01 * (float)(line[i*3 + 1] - '0'));
                    }
//                    std::cout << line << std::endl;
                }
                fp.close();
            }
        }
        catch (...) {
            std::cout << "Failed to open status file" << std::endl;
        }

        if ((int)(status * 100) != last) {
            last = (int)(status * 100);
            ui->progressBar->setValue(last);
        }


        if (status * 100 >= 99 || stop_flag) {
            std::string cmd = "taskkill /pid " + std::to_string(pi.dwProcessId) + " /t /f";
            const char *charCmd = cmd.c_str();
//            std::system(charCmd);
            WinExec(charCmd, SW_HIDE);
            CloseHandle(pi.hProcess);
            CloseHandle(pi.hThread);
            ui->startButton->setEnabled(true);
            processFlag = false;
            stop_flag = false;
            ui->stopButton->setEnabled(false);
            ui->progressBar->setValue(100);

        }
    }


//        if (strcmp(last, chBuf) != 0) {
//            mtx.lock();

//            std::cout << chBuf << std::endl;
//            memcpy(last, chBuf, BUFSIZE);
//        }
}

void MainWindow::on_startButton_clicked()
{
    StartDiag popup;
    QString digital = "";
    QString timing_string = "";
    QString groups = "";
    QString states = "";

    if (analysis_flag) {
        timing_string = "-t \"" + ui->flagTimeIn->text() + ", " + ui->pressDebounceIn->text() +
                        ", " + ui->openDebounceIn->text() + ", " + ui->timeoutIn->text() + "\"";
    }
    if (sliding_flag == true) {
        timing_string += " -s";
    }
    if (zone_flag) {
        states = "-u \"" + ui->analogZones->text() + ";" + ui->digitalZones->text() + "\"";
    }

    // Check that open and save have been completed
    QString err = "Failed to start...\n";

    if (!checkOpen) {
        err += "No input files are selected\n";

        if (!checkSave)
            err += "No save directory has been selected\n";
    }
   else if (!checkSave) {
        err += "No save directory has been selected\n";
    }

    if (ui->groupsIn->text().length() > 1)
        groups = "-g \"" + ui->groupsIn->text() + "\"";
    else
        err += "No groups entered";

    if (ui->digitalIn->text().length() > 1)
        digital = "-d \"" + ui->digitalIn->text() + "\"";


    if (err == "Failed to start...\n") {
        err = "\tNo errors detected\t\n";
        popup.msg(err);
        popup.exec();
    }
    else {
        popup.msg(err);
        popup.exec();
        return;         // If there were errors, do not try to execute the command
    }

    // Command uses the options described by calling Cotact_Monitoring.py -h or in user manual
    // -f option rewuires that the first entry is the desired directory to save output followed by
    // a list of input files seperated by commas.
    QString cmd = "./Contact_Monitoring.exe -p 2 " + groups +
                  " " + timing_string + " " + digital + " -f \"";
    cmd += save_dir;
    pn = files.size();

    for (int i = 0; i < pn; i++) {
        cmd += "," + files[i];
    }
    cmd += "\"";

    // ******** Open process with no window **********
    QByteArray arr = cmd.toLocal8Bit();
    char *exe = arr.data();

    wchar_t wexe[arr.length()];
    mbstowcs(wexe, exe, arr.length()+1); //Plus null
    LPWSTR ptr = wexe;                      // Cast QString to LPWSTR for windows.h


    std::ofstream ofs("status.txt");
    for (int i = 0; i < pn-1; i++)
        ofs << "00,";
    ofs << "00";
    ofs.close();

// How to capure input and output and start windows process
// https://learn.microsoft.com/en-us/windows/win32/procthread/creating-a-child-process-with-redirected-input-and-output?redirectedfrom=MSDN

    STARTUPINFO si;
    ZeroMemory( &pi, sizeof(pi) );

    ZeroMemory( &si, sizeof(si) );
    si.cb = sizeof(si);


    // Start the child process.
    if(!CreateProcess( NULL,    // No module name (use command line)
        ptr,                    // Command line
        NULL,                   // Process handle not inheritable
        NULL,                   // Thread handle not inheritable
        FALSE,                  // Set handle inheritance to TRUE
        CREATE_NO_WINDOW,       // No creation flags CREATE_NO_WINDOW
        NULL,                   // Use parent's environment block
        NULL,                   // Use parent's starting directory
        &si,                    // Pointer to STARTUPINFO structure
        &pi )                   // Pointer to PROCESS_INFORMATION structure
    )
    {
        std::cout << "CreateProcess failed" << std::endl;
        std::cout << "Command:\t";
        std::cout << exe << std::endl;
        return;
    }

    // Ensure that the stop button and stop flag are reset before starting a new process
    ui->stopButton->setEnabled(true);
    stop_flag = false;
    // Disable the start button when a process is already running
    ui->startButton->setEnabled(false);
    processFlag = true;


//    std::cout << exe << std::endl;



//    std::array<char, 128> buff;
//    QString ret = "";
//    FILE *p = popen(exe, "r");

//    std::cout << exe << std::endl;

//    while (fgets(buff.data(), 128, p) != NULL){
//        std::cout << buff.data() << std::endl;
//        fflush(stdout);
//        ret += buff.data();
//    }
//    pclose(p);
}



void MainWindow::on_actionExit_triggered()
{
    MainWindow::close();
}

void MainWindow::on_actionOpen_triggered()
{

    files = QFileDialog::getOpenFileNames(this, tr("Data Files to Use"),
                                          "./", tr("Data (*.csv *.bin)"));
    if (!files.isEmpty()) {                                                         // If files were selected
        checkOpen = true;
        ui->selected_files->setText("Selected input files:\n");
        for (int i = 0; i < files.size(); i++) {                                    // Iterates through the selected files
            ui->selected_files->setText(ui->selected_files->text() +
                                        "\n" + files[i]);
        }
    }
    else {
        ui->selected_files->setText("No files were selected");
        checkOpen = false;
    }

}

void MainWindow::on_actionSave_triggered()
{
    save_dir = QFileDialog::getExistingDirectory(this, tr("Select directory to save to"),
                                                "./", QFileDialog::ShowDirsOnly
                                                | QFileDialog::DontResolveSymlinks);

    if (!save_dir.isEmpty()) {
        ui->save_selection->setText("Selected save directory:\t" + save_dir);
        checkSave = true;
    }
    else {
        ui->selected_files->setText("No files were selected");
        checkSave = false;
    }


}


void MainWindow::on_analysisCheckBox_stateChanged(int flag)
{
    if (flag) {
        analysis_flag = true;
        ui->pressDebounceIn->setEnabled(true);
        ui->flagTimeIn->setEnabled(true);
        ui->isSliding->setEnabled(true);
        if (sliding_flag == false) {
            ui->openDebounceIn->setEnabled(true);
            ui->timeoutIn->setEnabled(true);
            ui->digitalIn->setEnabled(true);
        }

    }
    else {
        analysis_flag = false;
        ui->pressDebounceIn->setDisabled(true);
        ui->isSliding->setDisabled(true);
        ui->flagTimeIn->setDisabled(true);
        ui->openDebounceIn->setDisabled(true);
        ui->timeoutIn->setDisabled(true);
        ui->digitalIn->setDisabled(true);

    }
}


void MainWindow::on_isSliding_clicked(bool checked)
{
    sliding_flag = checked;
    ui->openDebounceIn->setDisabled(checked);
    ui->timeoutIn->setDisabled(checked);
    ui->digitalIn->setDisabled(checked);
}

void MainWindow::on_doZones_clicked(bool checked)
{
    zone_flag = checked;
    ui->analogZones->setEnabled(checked);
    ui->digitalZones->setEnabled(checked);
}

void MainWindow::on_pushButtonConfig_clicked()
{
    ui->flagTimeIn->setValue(7);
    ui->pressDebounceIn->setValue(5);
    ui->openDebounceIn->setValue(5);
    ui->timeoutIn->setValue(30);

    ui->groupsIn->setText("10, 11, 12; 20, 21, 22; 30, 31, 32; 40, 41, 42");
    ui->digitalIn->setText("12, 22, 32, 42");

    ui->analysisCheckBox->setCheckState(Qt::Checked);
    ui->isSliding->setEnabled(false);
    ui->isSliding->setCheckState(Qt::Unchecked);
    on_analysisCheckBox_stateChanged(1);
    on_isSliding_clicked(0);
}

void MainWindow::on_slidingConfig_clicked()
{
    ui->flagTimeIn->setValue(7);
    ui->pressDebounceIn->setValue(5);
    ui->openDebounceIn->setValue(5);
    ui->timeoutIn->setValue(30);

    ui->groupsIn->setText("10; 20; 30; 40; 50; 60");
    ui->digitalIn->setText("");

    ui->analysisCheckBox->setCheckState(Qt::Checked);
    ui->isSliding->setEnabled(true);
    ui->isSliding->setCheckState(Qt::Checked);
    on_analysisCheckBox_stateChanged(1);
    on_isSliding_clicked(1);
}

void MainWindow::on_stopButton_clicked()
{
    stop_flag = true;
    ui->stopButton->setEnabled(false);
}
