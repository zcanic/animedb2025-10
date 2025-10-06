// Define database connection via the `DATABASE_URL` env var
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

// Define custom output path for generated Prisma Client
generator client {
  provider = "prisma-client-js"
  output   = "/app/generated/prisma-client"
}

// Example data model
model User {
  id        Int      @id @default(autoincrement())
  createdAt DateTime @default(now())
  email     String   @unique
  name      String?
}

# Run in terminal to generate Prisma Client
# into the output path: `app/generated-prisma-client`
npx prisma generate --no-engine

import { PrismaClient } from 'app/generated-prisma-client'
import { withAccelerate } from '@prisma/extension-accelerate'

const prisma = new PrismaClient().$extends(withAccelerate())

const users = await prisma.user.findMany({
  where: {
    email: { endsWith: "prisma.io" }
  },
})



1

Set up a Next.js project

Use create-next-app to create a Next.js CRUD demo with Prisma Postgres using the official Next.js example with Prisma Postgres, navigate into the project directory and install dependencies:


npx create-next-app@latest --template prisma-postgres my-prisma-postgres-app
cd my-prisma-postgres-app
npm install
2

Connect Vercel project

Connect the my-prisma-postgres-app application on your local machine with a project in your Vercel team by running the following command:


vercel link
3

Pull the database URL from Vercel

Now you can pull the DATABASE_URL environment variable from Vercel like so:


vercel env pull .env.development.local
This will update your local .env file and configure your database connection to this Prisma Postgres instance.

4

Run migrations and seed the database

Create the database schema in your Prisma Postgres instance by running a migration:


npx prisma migrate dev --name init
This will create a local SQL migration file and apply it against your remote database. Now, create some sample data so the UI won’t look empty when you run the app:


npx prisma db seed
5

Deploy the app to Vercel

Finally, you can use the vercel CLI to deploy your application:

vercel deploy
