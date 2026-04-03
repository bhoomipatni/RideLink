CREATE TABLE "Users"(
    "username" VARCHAR(255) NOT NULL,
    "rcsid" VARCHAR(255) NOT NULL,
    "isdriver" BOOLEAN NOT NULL,
    "rides" INTEGER[] NOT NULL
);
ALTER TABLE
    "Users" ADD CONSTRAINT "users_username_unique" UNIQUE("username");
ALTER TABLE
    "Users" ADD CONSTRAINT "users_rcsid_unique" UNIQUE("rcsid");
CREATE TABLE "Rides"(
    "id" SERIAL NOT NULL,
    "date" DATE NOT NULL,
    "driverid" BIGINT NOT NULL,
    "address" VARCHAR(255) NOT NULL,
    "cost" FLOAT(53) NOT NULL,
    "isactive" BOOLEAN NOT NULL,
    "description" VARCHAR(255) NOT NULL,
    "lat" FLOAT(53) NOT NULL,
    "long" FLOAT(53) NOT NULL,
    "riders" INTEGER[] NOT NULL,
    "orgin" VARCHAR(255) NOT NULL
);
ALTER TABLE
    "Rides" ADD CONSTRAINT "rides_id_unique" UNIQUE("id");
CREATE TABLE "Notifcations"(
    "rcsid" VARCHAR(255) NOT NULL,
    "rideid" BIGINT NOT NULL,
    "status" VARCHAR(255) NOT NULL
);