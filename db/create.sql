-- Feel free to modify this file to match your development goal.
-- Here we only create 3 tables for demo purpose.

CREATE TABLE Users (
    id INT NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
    email VARCHAR UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    firstname VARCHAR(255) NOT NULL,
    lastname VARCHAR(255) NOT NULL, 
    address VARCHAR(255) NOT NULL, --added field--
    is_seller BOOLEAN DEFAULT FALSE --added field--
);

CREATE TABLE Categories (
    cid INT NOT NULL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    parent_id INT DEFAULT NULL REFERENCES Categories(cid)
);


CREATE TABLE Products (
    pid INT NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
    cid INT NOT NULL REFERENCES Categories(cid),
    creator_id INT NOT NULL REFERENCES Users(id), 
    name VARCHAR(1000) UNIQUE NOT NULL,
    -- price DECIMAL(12,2) NOT NULL,
    description VARCHAR(100000) NOT NULL, 
    image VARCHAR(10000) DEFAULT NULL,
    available BOOLEAN DEFAULT TRUE
);

CREATE TABLE Inventory (
    pid INT NOT NULL REFERENCES Products(pid),
    seller_id INT NOT NULL REFERENCES Users(id),
    unit_price FLOAT NOT NULL CHECK (unit_price >= 0),
    quantity INT NOT NULL CHECK (quantity >= 0),
    PRIMARY KEY (pid, seller_id)
);

-- CREATE TABLE Purchases (
--     id INT NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
--     uid INT NOT NULL REFERENCES Users(id),
--     pid INT NOT NULL REFERENCES Products(id),
--     time_purchased timestamp without time zone NOT NULL DEFAULT (current_timestamp AT TIME ZONE 'UTC')
-- );

CREATE TABLE CartItem (
    uid INTEGER NOT NULL REFERENCES Users(id),
    pid INTEGER NOT NULL REFERENCES Products(pid),
    seller_id INTEGER NOT NULL REFERENCES Users(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price FLOAT NOT NULL CHECK (unit_price >= 0),
    date_added timestamp without time zone NOT NULL DEFAULT (current_timestamp AT TIME ZONE 'UTC'),
    saved_for_later BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (uid, pid, seller_id, saved_for_later)
);

CREATE TABLE Orders (
    order_id INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
    buyer_id INTEGER NOT NULL REFERENCES Users(id),
    order_status BOOLEAN NOT NULL DEFAULT FALSE,
    order_date timestamp without time zone NOT NULL DEFAULT (current_timestamp AT TIME ZONE 'UTC')
);

CREATE TABLE OrderItem (
    order_id INTEGER NOT NULL REFERENCES Orders(order_id),
    pid INTEGER NOT NULL REFERENCES Products(pid),
    seller_id INTEGER NOT NULL REFERENCES Users(id),
    quantity INTEGER NOT NULL CHECK (quantity >= 0),
    unit_price FLOAT NOT NULL CHECK (unit_price >= 0),
    fulfillment_status BOOLEAN NOT NULL DEFAULT FALSE,
    fulfillment_date timestamp without time zone DEFAULT (current_timestamp AT TIME ZONE 'UTC'),
    PRIMARY KEY (order_id, pid, seller_id)
);

CREATE TABLE Balances (
    uid INT NOT NULL REFERENCES Users(id),
    timestamp timestamp without time zone NOT NULL DEFAULT (current_timestamp AT TIME ZONE 'UTC'),
    amount FLOAT NOT NULL CHECK (amount >= 0),
    transaction VARCHAR(50) NOT NULL,
    related_order_id INT REFERENCES Orders(order_id) DEFAULT NULL, -- Reference to order id (optional, use NULL if not applicable)
    PRIMARY KEY (uid, timestamp)
);

CREATE TABLE ProductReviews (
    buyer_id INTEGER NOT NULL REFERENCES Users(id),
    pid INTEGER NOT NULL  REFERENCES Products(pid),
    title VARCHAR(1000),
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    message VARCHAR(100000) NOT NULL,
    upvote_count INTEGER NOT NULL CHECK (upvote_count >= 0),
    timestamp timestamp without time zone NOT NULL DEFAULT (current_timestamp AT TIME ZONE 'UTC'),
    PRIMARY KEY (buyer_id, pid)
);

CREATE TABLE SellerReviews (
    buyer_id INTEGER NOT NULL REFERENCES Users(id),
    seller_id INTEGER NOT NULL REFERENCES Users(id),
    title VARCHAR(1000),
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    message VARCHAR(100000),
    upvote_count INTEGER NOT NULL CHECK (upvote_count >= 0),
    timestamp timestamp without time zone NOT NULL DEFAULT (current_timestamp AT TIME ZONE 'UTC'),
    PRIMARY KEY (buyer_id, seller_id)
);

CREATE TABLE Wishlist (
    uid INT NOT NULL REFERENCES Users(id),
    pid INT NOT NULL REFERENCES Products(pid),
    time_added timestamp without time zone NOT NULL DEFAULT (current_timestamp AT TIME ZONE 'UTC'),
    PRIMARY KEY (uid, pid)
);

-- CREATE TABLE Purchases (
--     id INT NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
--     uid INT NOT NULL REFERENCES Users(id),
--     pid INT NOT NULL REFERENCES Products(id),
--     time_purchased timestamp without time zone NOT NULL DEFAULT (current_timestamp AT TIME ZONE 'UTC')
-- );


