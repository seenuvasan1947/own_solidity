// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// SCWE-021: Unsecured Data Transmission Test Cases

// Vulnerable: Unsecured data transmission
contract UnsecuredData {
    address public owner;
    mapping(address => string) public userData;

    constructor() {
        owner = msg.sender;
    }

    // Vulnerable: Transmit data without encryption
    function transmitData(bytes memory data) public {
        // Transmit data without encryption
        emit DataTransmitted(data);
    }

    // Vulnerable: Send sensitive information without encryption
    function sendPrivateKey(string memory privateKey) public {
        require(msg.sender == owner, "Not authorized");
        // Send private key without encryption
        emit PrivateKeySent(privateKey);
    }

    // Vulnerable: Transfer sensitive data without encryption
    function transferCredentials(string memory username, string memory password) public {
        // Transfer credentials without encryption
        emit CredentialsTransferred(username, password);
    }

    // Vulnerable: Broadcast sensitive information
    function broadcastSecret(string memory secret) public {
        // Broadcast secret without encryption
        emit SecretBroadcasted(secret);
    }

    // Vulnerable: Return sensitive data without encryption
    function getSensitiveData() public view returns (string memory) {
        return userData[msg.sender];
    }

    // Vulnerable: Export data without encryption
    function exportUserData(address user) public view returns (string memory) {
        return userData[user];
    }

    event DataTransmitted(bytes data);
    event PrivateKeySent(string privateKey);
    event CredentialsTransferred(string username, string password);
    event SecretBroadcasted(string secret);
}

// Secure: Encrypted data transmission
contract SecuredData {
    address public owner;
    mapping(address => bytes) public encryptedUserData;

    constructor() {
        owner = msg.sender;
    }

    // Secure: Transmit encrypted data
    function transmitData(bytes memory encryptedData) public {
        // Transmit encrypted data
        emit EncryptedDataTransmitted(encryptedData);
    }

    // Secure: Send encrypted private key
    function sendPrivateKey(bytes memory encryptedPrivateKey) public {
        require(msg.sender == owner, "Not authorized");
        // Send encrypted private key
        emit EncryptedPrivateKeySent(encryptedPrivateKey);
    }

    // Secure: Transfer encrypted credentials
    function transferCredentials(bytes memory encryptedCredentials) public {
        // Transfer encrypted credentials
        emit EncryptedCredentialsTransferred(encryptedCredentials);
    }

    // Secure: Broadcast encrypted secret
    function broadcastSecret(bytes memory encryptedSecret) public {
        // Broadcast encrypted secret
        emit EncryptedSecretBroadcasted(encryptedSecret);
    }

    // Secure: Return encrypted data
    function getSensitiveData() public view returns (bytes memory) {
        return encryptedUserData[msg.sender];
    }

    // Secure: Export encrypted data
    function exportUserData(address user) public view returns (bytes memory) {
        return encryptedUserData[user];
    }

    // Secure: Hash sensitive data before transmission
    function transmitHashedData(string memory data) public {
        bytes32 hashedData = keccak256(abi.encodePacked(data));
        emit HashedDataTransmitted(hashedData);
    }

    event EncryptedDataTransmitted(bytes encryptedData);
    event EncryptedPrivateKeySent(bytes encryptedPrivateKey);
    event EncryptedCredentialsTransferred(bytes encryptedCredentials);
    event EncryptedSecretBroadcasted(bytes encryptedSecret);
    event HashedDataTransmitted(bytes32 hashedData);
}

// Mixed: Some secure, some vulnerable
contract MixedDataTransmission {
    address public owner;
    mapping(address => string) public userData;
    mapping(address => bytes) public encryptedUserData;

    constructor() {
        owner = msg.sender;
    }

    // Secure: Encrypted transmission
    function transmitEncryptedData(bytes memory encryptedData) public {
        emit EncryptedDataTransmitted(encryptedData);
    }

    // Vulnerable: Unencrypted transmission
    function transmitPlainData(string memory data) public {
        emit PlainDataTransmitted(data);
    }

    // Secure: Hash before transmission
    function transmitHashedData(string memory data) public {
        bytes32 hashedData = keccak256(abi.encodePacked(data));
        emit HashedDataTransmitted(hashedData);
    }

    // Vulnerable: Return unencrypted data
    function getPlainData() public view returns (string memory) {
        return userData[msg.sender];
    }

    // Secure: Return encrypted data
    function getEncryptedData() public view returns (bytes memory) {
        return encryptedUserData[msg.sender];
    }

    event EncryptedDataTransmitted(bytes encryptedData);
    event PlainDataTransmitted(string data);
    event HashedDataTransmitted(bytes32 hashedData);
}

// Functions that don't handle sensitive data (should not be flagged)
contract NonSensitiveFunctions {
    address public owner;
    uint public balance;

    constructor() {
        owner = msg.sender;
    }

    function deposit() public payable {
        balance += msg.value;
    }

    function withdraw(uint amount) public {
        require(msg.sender == owner, "Not authorized");
        balance -= amount;
        payable(msg.sender).transfer(amount);
    }

    function getBalance() public view returns (uint) {
        return balance;
    }

    function isOwner() public view returns (bool) {
        return msg.sender == owner;
    }
}
