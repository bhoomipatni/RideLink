CREATE TABLE "Users"(
    "username" VARCHAR(255) NOT NULL,
    "rcsid" VARCHAR(255) NOT NULL,
    "isdriver" BOOLEAN NOT NULL,
    "rides" INTEGER[] NOT NULL,
    "venmo_username" VARCHAR(50) NULL,
    "paypal_email" VARCHAR(255) NULL,
    "accepts_cash" BOOLEAN DEFAULT FALSE
);
ALTER TABLE
    "Users" ADD CONSTRAINT "users_username_unique" UNIQUE("username");
ALTER TABLE
    "Users" ADD CONSTRAINT "users_rcsid_unique" UNIQUE("rcsid");
CREATE TABLE "Rides"(
    "id" SERIAL NOT NULL,
    "date" DATE NOT NULL,
    "driverid" VARCHAR(255) NOT NULL,
    "address" VARCHAR(255) NOT NULL,
    "cost" FLOAT(53) NOT NULL,
    "isactive" BOOLEAN NOT NULL,
    "description" VARCHAR(255) NOT NULL,
    "lat" FLOAT(53) NOT NULL,
    "long" FLOAT(53) NOT NULL,
    "riders" VARCHAR(255)[] NOT NULL,
    "orgin" VARCHAR(255) NOT NULL
);
ALTER TABLE
    "Rides" ADD CONSTRAINT "rides_id_unique" UNIQUE("id");
CREATE TABLE "Notifications"(
    "rcsid" VARCHAR(255) NOT NULL,
    "rideid" BIGINT NOT NULL,
    "status" VARCHAR(255) NOT NULL,
    PRIMARY KEY ("rcsid", "rideid")
);