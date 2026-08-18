CREATE TABLE `categories`(
    `CategoryID` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `CategoryName` VARCHAR(255) NOT NULL
);
CREATE TABLE `orders`(
    `OrderID` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `CustomerID` BIGINT NOT NULL,
    `OrderDate` DATE NOT NULL,
    `OrderTime` TIME NOT NULL
);
CREATE TABLE `customers`(
    `CustomerID` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `Gender` CHAR(255) NOT NULL,
    `Age` BIGINT NOT NULL,
    `City` VARCHAR(255) NOT NULL,
    `Region` VARCHAR(255) NOT NULL,
    `CustomerSegment` VARCHAR(255) NOT NULL,
    `SignUpDate` DATE NOT NULL
);
CREATE TABLE `order_details`(
    `OrderID` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `ProductID` BIGINT NOT NULL,
    `Quantity` BIGINT NOT NULL,
    `UnitCost` FLOAT(53) NOT NULL,
    `UnitPrice` FLOAT(53) NOT NULL,
    `DiscountRate` FLOAT(53) NOT NULL,
    `IsReturned` BOOLEAN NOT NULL,
    `ReturnDate` DATE NOT NULL,
    `ReturnTime` TIME NOT NULL,
    `ReturnReason` VARCHAR(255) NOT NULL,
    PRIMARY KEY(`ProductID`)
);
CREATE TABLE `products`(
    `ProductID` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `ProductName` VARCHAR(255) NOT NULL,
    `CategoryID` BIGINT NOT NULL
);
ALTER TABLE
    `order_details` ADD CONSTRAINT `order_details_orderid_foreign` FOREIGN KEY(`OrderID`) REFERENCES `orders`(`OrderID`);
ALTER TABLE
    `order_details` ADD CONSTRAINT `order_details_productid_foreign` FOREIGN KEY(`ProductID`) REFERENCES `products`(`ProductID`);
ALTER TABLE
    `orders` ADD CONSTRAINT `orders_customerid_foreign` FOREIGN KEY(`CustomerID`) REFERENCES `customers`(`CustomerID`);
ALTER TABLE
    `products` ADD CONSTRAINT `products_categoryid_foreign` FOREIGN KEY(`CategoryID`) REFERENCES `categories`(`CategoryID`);