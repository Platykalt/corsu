#include <QCoreApplication>
#include <KLocalizedString>
#include <iostream>
int main(int argc, char **argv) {
    QCoreApplication app(argc, argv);
    KLocalizedString::setLanguages({QStringLiteral("co"), QStringLiteral("fr")});
    const auto value = ki18nd("kconfigwidgets6", "&Save").toString();
    std::cout << value.toStdString() << std::endl;
    return value == QString::fromUtf8("Salvà") ? 0 : 1;
}
