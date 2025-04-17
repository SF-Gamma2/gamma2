const jsforce = require('jsforce');
const ftp = require('basic-ftp');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const { createObjectCsvWriter } = require('csv-writer');

// Configuration
const config = {
    salesforce: {
        username: process.env.SF_USERNAME,
        password: process.env.SF_PASSWORD,
        securityToken: process.env.SF_SECURITY_TOKEN,
        loginUrl: process.env.SF_LOGIN_URL || 'https://login.salesforce.com'
    },
    shutterstock: {
        ftpHost: process.env.SS_FTP_HOST,
        ftpUser: process.env.SS_FTP_USER,
        ftpPassword: process.env.SS_FTP_PASSWORD,
        ftpPort: process.env.SS_FTP_PORT || 21
    }
};

async function transferData() {
    try {
        // 1. Connect to Salesforce and get data
        const conn = new jsforce.Connection({
            loginUrl: config.salesforce.loginUrl
        });
        
        await conn.login(
            config.salesforce.username,
            config.salesforce.password + config.salesforce.securityToken
        );
        
        const result = await conn.apex.get('/ShutterstockTransferController/getLatestPromptData');
        
        console.log('Retrieved data from Salesforce:', result);
        
        // 2. Process image
        if (result.imageUrl) {
            const imageResponse = await axios.get(result.imageUrl, {
                responseType: 'arraybuffer'
            });
            
            const imageBuffer = Buffer.from(imageResponse.data, 'binary');
            const imageFilename = `${result.recordName || 'image'}_${Date.now()}.jpg`;
            
            // 3. Process CSV
            const csvFilename = `${result.recordName || 'data'}_${Date.now()}.csv`;
            const csvPath = path.join(__dirname, csvFilename);
            
            // The CSV content is already formatted, just write it directly
            fs.writeFileSync(csvPath, result.csvContent);
            
            // 4. Connect to Shutterstock FTP
            const client = new ftp.Client();
            client.ftp.verbose = true;
            
            await client.access({
                host: config.shutterstock.ftpHost,
                user: config.shutterstock.ftpUser,
                password: config.shutterstock.ftpPassword,
                port: config.shutterstock.ftpPort,
                secure: false
            });
            
            // Upload files
            await client.uploadFrom(imageBuffer, imageFilename);
            await client.uploadFrom(csvPath, csvFilename);
            
            console.log('Files transferred successfully:', imageFilename, csvFilename);
            
            // Clean up
            client.close();
            fs.unlinkSync(csvPath);
        } else {
            console.log('No image URL found in the record');
        }
        
    } catch (error) {
        console.error('Error during transfer:', error);
        throw error;
    }
}

// Run the transfer
transferData();
