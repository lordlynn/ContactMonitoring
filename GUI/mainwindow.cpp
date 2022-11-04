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

// Setting up windows process and sdtin/stdout
#define BUFSIZE 4096

//CHAR chBuf[BUFSIZE];
//std::mutex mtx;

HANDLE g_hChildStd_IN_Rd = NULL;
HANDLE g_hChildStd_IN_Wr = NULL;
HANDLE g_hChildStd_OUT_Rd = NULL;
HANDLE g_hChildStd_OUT_Wr = NULL;
HANDLE g_hInputFile = NULL;

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
//float *states;


MainWindow::MainWindow(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::MainWindow)
{

    // Calls the checkThread slot periodically
    QTimer *timer = new QTimer(this);
    connect(timer, &QTimer::timeout, this, MainWindow::checkThread);
    timer->start(1000);

    ui->setupUi(this);
}

MainWindow::~MainWindow()
{
    delete ui;
}


void MainWindow::checkThread()
{
//    static CHAR last[BUFSIZE];
    float status = 0.0;
    static int last = 0.0;

    if (processFlag) {
        try {
            std::string line;
            std::ifstream fp("status.txt");
            if (fp.is_open()) {
                while (std::getline(fp, line)) {
                    for (int i = 0; i < pn; i++) {
                        status += (1 / (float)pn) * (0.1 * (float)(line[i*3] - '0') + 0.01 * (float)(line[i*3 + 1] - '0'));
//                        states[i] = 0.1 * (line[i*3] - '0') + 0.01 * (line[i*3 + 1] - '0');
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


        if (WaitForSingleObject(pi.hProcess, 0) == 0 || status * 100 >= 99) {
            ui->startButton->setEnabled(true);
            TerminateProcess(pi.hProcess, 0);
            CloseHandle(pi.hProcess);
            processFlag = false;
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

    if (analysis_flag) {
        timing_string = "-t \"" + ui->flagTimeIn->text() + ", " + ui->pressDebounceIn->text() +
                        ", " + ui->openDebounceIn->text() + ", " + ui->timeoutIn->text() + "\"";
    }
    if (sliding_flag == true) {
        timing_string += " -s";
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
    QString cmd = "python ./Contact_Monitoring.py -p 1 " + groups +
                  " " + timing_string + " " + digital + " -f \"";
    cmd += save_dir;
    pn = files.size();
//    states = (float*) calloc(pn, sizeof(float));
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



// How to capure input and output
// https://learn.microsoft.com/en-us/windows/win32/procthread/creating-a-child-process-with-redirected-input-and-output?redirectedfrom=MSDN

//    //-------- Create Pipes for when a child process is started --------
//    SECURITY_ATTRIBUTES saAttr;

//    // Set the bInheritHandle flag so pipe handles are inherited.
//    saAttr.nLength = sizeof(SECURITY_ATTRIBUTES);
//    saAttr.bInheritHandle = TRUE;
//    saAttr.lpSecurityDescriptor = NULL;

//    // Create a pipe for the child process's STDOUT.
//    if ( ! CreatePipe(&g_hChildStd_OUT_Rd, &g_hChildStd_OUT_Wr, &saAttr, 0) )
//        ErrorExit(TEXT("StdoutRd CreatePipe"));

//    // Ensure the read handle to the pipe for STDOUT is not inherited.
//    if ( ! SetHandleInformation(g_hChildStd_OUT_Rd, HANDLE_FLAG_INHERIT, 0) )
//        ErrorExit(TEXT("Stdout SetHandleInformation"));

//    // Create a pipe for the child process's STDIN.
//    if (! CreatePipe(&g_hChildStd_IN_Rd, &g_hChildStd_IN_Wr, &saAttr, 0))
//        ErrorExit(TEXT("Stdin CreatePipe"));

//    // Ensure the write handle to the pipe for STDIN is not inherited.
//    if ( ! SetHandleInformation(g_hChildStd_IN_Wr, HANDLE_FLAG_INHERIT, 0) )
//        ErrorExit(TEXT("Stdin SetHandleInformation"));


//    STARTUPINFO siStartInfo;

    // Set up members of the STARTUPINFO structure.
    // This structure specifies the STDIN and STDOUT handles for redirection.
//    ZeroMemory(&siStartInfo, sizeof(STARTUPINFO));
//    siStartInfo.cb = sizeof(STARTUPINFO);
//    siStartInfo.hStdError = g_hChildStd_OUT_Wr;
//    siStartInfo.hStdOutput = g_hChildStd_OUT_Wr;
//    siStartInfo.hStdInput = g_hChildStd_IN_Rd;
//    siStartInfo.dwFlags |= STARTF_USESTDHANDLES;


//    PROCESS_INFORMATION pi;   // GLOBAL
    STARTUPINFO si;
    ZeroMemory( &pi, sizeof(pi) );

    ZeroMemory( &si, sizeof(si) );
    si.cb = sizeof(si);


    // Start the child process.
    if(!CreateProcess( NULL,    // No module name (use command line)
        ptr,                    // Command line
        NULL,                   // Process handle not inheritable
        NULL,                   // Thread handle not inheritable
        FALSE,                   // Set handle inheritance to TRUE
        CREATE_NO_WINDOW,       // No creation flags CREATE_NO_WINDOW
        NULL,                   // Use parent's environment block
        NULL,                   // Use parent's starting directory
        &si,                    // Pointer to STARTUPINFO structure
        &pi )                   // Pointer to PROCESS_INFORMATION structure
    )
    {
        std::cout << "CreateProcess failed" << std::endl;
        return;
    }

    ui->startButton->setEnabled(false);


//    QString tmp = "./pipe.txt";
//    QByteArray tmp_arr = tmp.toLocal8Bit();
//    char *tmp_name = tmp_arr.data();

//    wchar_t fn[tmp_arr.length()];
//    mbstowcs(fn, tmp_name, tmp_arr.length()+1); //Plus null
//    LPWSTR filename = fn;

//    g_hInputFile = CreateFile(
//        filename,
//        GENERIC_READ,
//        0,
//        NULL,
//        OPEN_EXISTING,
//        FILE_ATTRIBUTE_READONLY,
//        NULL);

//    if (g_hInputFile == INVALID_HANDLE_VALUE)
//        ErrorExit(TEXT("CreateFile"));


    // Wait until child process exits.
//    WaitForSingleObject( pi.hProcess, INFINITE );

    // Close process and thread handles.


//    CloseHandle( pi.hProcess );
    CloseHandle( pi.hThread );




//    CloseHandle(g_hChildStd_OUT_Wr);
//    CloseHandle(g_hChildStd_IN_Rd);

//    auto t = std::async(&MainWindow::ReadFromPipe, this);
//    std::thread t(&MainWindow::ReadFromPipe, this, chBuf);
//    t.detach();
    processFlag = true;
//    auto ret = t.get();
    std::cout << exe << std::endl;



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

void MainWindow::ReadFromPipe(CHAR buf[]) {
    // Read output from the child process's pipe for STDOUT
    // and write to the parent process's pipe for STDOUT.
    // Stop when there is no more data.
    DWORD dwRead, dwWritten;
//    CHAR chBuf[BUFSIZE];
    BOOL bSuccess = FALSE;
    HANDLE hParentStdOut = GetStdHandle(STD_OUTPUT_HANDLE);


//    int i = 0;
    for (;;) {
//        mtx.lock();
        bSuccess = ReadFile( g_hChildStd_OUT_Rd, buf, BUFSIZE, &dwRead, NULL);

        if( ! bSuccess || dwRead == 0 ) break;
//        std::cout << i << std::endl;
//        mtx.unlock();
//        std::cout << chBuf << std::endl;
//        bSuccess = WriteFile(hParentStdOut, chBuf,
//                           dwRead, &dwWritten, NULL);
//        if (! bSuccess ) return;
    }
}

void MainWindow::ErrorExit(PTSTR lpszFunction)
// Format a readable error message, display a message box,
// and exit from the application.
{
    LPVOID lpMsgBuf;
    LPVOID lpDisplayBuf;
    DWORD dw = GetLastError();

    FormatMessage(
        FORMAT_MESSAGE_ALLOCATE_BUFFER |
        FORMAT_MESSAGE_FROM_SYSTEM |
        FORMAT_MESSAGE_IGNORE_INSERTS,
        NULL,
        dw,
        MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
        (LPTSTR) &lpMsgBuf,
        0, NULL );

    lpDisplayBuf = (LPVOID)LocalAlloc(LMEM_ZEROINIT,
        (lstrlen((LPCTSTR)lpMsgBuf)+lstrlen((LPCTSTR)lpszFunction)+40)*sizeof(TCHAR));
    StringCchPrintf((LPTSTR)lpDisplayBuf,
        LocalSize(lpDisplayBuf) / sizeof(TCHAR),
        TEXT("%s failed with error %d: %s"),
        lpszFunction, dw, lpMsgBuf);
    MessageBox(NULL, (LPCTSTR)lpDisplayBuf, TEXT("Error"), MB_OK);

    LocalFree(lpMsgBuf);
    LocalFree(lpDisplayBuf);
    ExitProcess(1);
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
    ui->zones->setEnabled(checked);
}
