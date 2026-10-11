
USE FraudDetection;
GO
IF SCHEMA_ID('fds') IS NULL EXEC('CREATE SCHEMA fds');
GO

IF OBJECT_ID('fds.Customers','U') IS NULL
CREATE TABLE fds.Customers (
    CustomerId  INT IDENTITY(1,1) PRIMARY KEY,
    Name        NVARCHAR(150) NOT NULL,
    HomeCountry CHAR(2)       NOT NULL,
    RiskRating  VARCHAR(10)   NOT NULL DEFAULT 'LOW'
);
GO

IF OBJECT_ID('fds.Accounts','U') IS NULL
CREATE TABLE fds.Accounts (
    AccountId     INT IDENTITY(1,1) PRIMARY KEY,
    CustomerId    INT NOT NULL REFERENCES fds.Customers(CustomerId),
    AccountNumber VARCHAR(30)   NOT NULL UNIQUE,
    Balance       DECIMAL(19,4) NOT NULL DEFAULT 0,
    Currency      CHAR(3)       NOT NULL DEFAULT 'ZAR',
    Status        VARCHAR(12)   NOT NULL DEFAULT 'ACTIVE'
);
GO

IF OBJECT_ID('fds.Transactions','U') IS NULL
CREATE TABLE fds.Transactions (
    TxnId        BIGINT IDENTITY(1,1) PRIMARY KEY,
    AccountId    INT NOT NULL REFERENCES fds.Accounts(AccountId),
    Amount       DECIMAL(19,4) NOT NULL,
    Channel      VARCHAR(10)   NOT NULL,
    Country      CHAR(2)       NOT NULL,
    Recipient    NVARCHAR(100) NULL,
    Currency     CHAR(3)       NOT NULL DEFAULT 'ZAR',
    Status       VARCHAR(12)   NOT NULL DEFAULT 'PENDING',
    CreatedAt    DATETIME2(3)  NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

IF OBJECT_ID('fds.Evaluations','U') IS NULL
CREATE TABLE fds.Evaluations (
    TxnId         BIGINT PRIMARY KEY REFERENCES fds.Transactions(TxnId),
    RiskScore     DECIMAL(5,2) NOT NULL,
    Decision      VARCHAR(8)   NULL,
    BreachedRules NVARCHAR(400) NOT NULL DEFAULT '[]',   -- JSON array of rule names
    EvaluatedAt   DATETIME2(3) NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

IF OBJECT_ID('fds.Alerts','U') IS NULL
CREATE TABLE fds.Alerts (
    AlertId   BIGINT IDENTITY(1,1) PRIMARY KEY,
    TxnId     BIGINT NOT NULL REFERENCES fds.Transactions(TxnId),
    RuleName  NVARCHAR(100) NOT NULL,
    Severity  VARCHAR(10)   NULL,
    Status    VARCHAR(14)   NOT NULL DEFAULT 'OPEN',
    RaisedAt  DATETIME2(3)  NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

IF OBJECT_ID('fds.Cases','U') IS NULL
CREATE TABLE fds.Cases (
    CaseId       INT IDENTITY(1,1) PRIMARY KEY,
    AssignedTo   INT NULL,
    Status       VARCHAR(12)   NOT NULL DEFAULT 'OPEN',
    AlertIdsJson NVARCHAR(MAX) NOT NULL DEFAULT '[]',
    Resolution   NVARCHAR(500) NULL,
    OpenedAt     DATETIME2(3)  NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

IF OBJECT_ID('fds.Notifications','U') IS NULL
CREATE TABLE fds.Notifications (
    NotificationId BIGINT IDENTITY(1,1) PRIMARY KEY,
    TxnId     BIGINT NOT NULL REFERENCES fds.Transactions(TxnId),
    Recipient NVARCHAR(100) NOT NULL,
    Channel   VARCHAR(10)   NOT NULL,
    Message   NVARCHAR(400) NOT NULL,
    SentAt    DATETIME2(3)  NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

IF OBJECT_ID('fds.AuditEntries','U') IS NULL
CREATE TABLE fds.AuditEntries (
    EntryId    BIGINT IDENTITY(1,1) PRIMARY KEY,
    EntityType VARCHAR(50)   NOT NULL,
    EntityId   BIGINT        NOT NULL,
    Action     VARCHAR(20)   NOT NULL,
    Actor      NVARCHAR(100) NOT NULL,
    OldValue   NVARCHAR(MAX) NULL,
    NewValue   NVARCHAR(MAX) NULL,
    Hash       CHAR(64)      NOT NULL,
    Timestamp  DATETIME2(3)  NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

PRINT 'fds schema ready.';
GO
