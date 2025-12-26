<p align="center">
  <a href="README-TR.md">Türkçe</a><br>
</p>
# wraith-app (Unofficial)

> ⚠️ **Unofficial Project Warning**  
> This application is a **Wraith** keyboard application and works **only with the Wraith W75**; however, it is **not developed by the official Wraith developers**.  
> It is **not an official application** and has **no official affiliation with Wraith**.

---

## 📌 About the Project

**wraith-app** is a **community-developed (unofficial)** desktop version of the Wraith keyboard application.

With this project, users can:

- **Build the application as an exe themselves**
- Or **download and use precompiled versions**

Prebuilt versions are available as:

- **Installer version**
- **Portable version**

---

## 🚀 Installation and Usage

There are two different ways to use the application.

---

## 🔧 1. Build from Source  
### (For Those Who Want to Create an EXE)

Thanks to the **build.bat** file, this project can **automatically generate an exe without entering any manual commands**.

### Requirements

- **Windows**
- **Node.js** (LTS version recommended)  
  👉 https://nodejs.org
- Internet connection (required for first-time setup)

---

### ⚙️ Creating the EXE (Recommended Method)

1. **Download all files** in this repository or clone the project  
2. **Double-click the `build.bat` file** located in the project folder  
3. Windows may ask for **Administrator permission** (automatically)  
4. The script will automatically:
   - Run `npm install`
   - Build the project with `npm run dist`
5. When the process is complete, **your exe file will be created**

🟢 No extra commands are required  
🟢 All steps are handled automatically  

---

### ℹ️ What Does build.bat Do?

The `build.bat` file:

- Checks for administrator privileges  
- Switches to the correct project directory  
- Installs required npm packages  
- Starts the build (exe) process  
- Notifies the user of success or failure  

On success:

BUILD SUCCESSFUL

On failure:

BUILD FAILED!

---

## 📦 2. Prebuilt Versions (Recommended)

For users who do not want to install Node.js or build the project themselves, **precompiled versions** are available.

### Available Version Types

#### 🧩 Installer Version
- Installs on the computer  
- Added to the Start Menu  
- Includes uninstall support  

#### 📁 Portable Version
- No installation required  
- Download and run directly  
- Can even run from a USB drive  

---

### 📥 Download

1. Go to the **Releases** section on the GitHub page  
2. Choose the version you want:
   - **Installer**
   - **Portable**
3. Download and run  

👉 **No additional setup required.**

---

## 📁 Releases

All prebuilt versions are shared in the **Releases** section.

Each release includes:

- Installer / portable options  
- Release notes  
- Changes made  
- Bug fixes  

---

## 🛠️ Technologies Used

- **Node.js**
- **Electron**

---

## ❗ Disclaimer

- This project is **not official**
- It does not replace the official Wraith application
- The project developers cannot be held responsible for any issues that may occur

---

## 🤝 Contributing

Contributions are always welcome 🙌

- You can submit Pull Requests  
- You can open Issues to report bugs  
- You can suggest improvements  

---

## 📄 License

This project is open source.  
For details, please see the **LICENSE** file.
