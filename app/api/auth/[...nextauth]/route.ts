// Import the necessary modules
import NextAuth, { NextAuthOptions } from "next-auth";
import { PrismaAdapter } from "@next-auth/prisma-adapter";
import prisma from "@/lib/prisma";
import GoogleProvider from "next-auth/providers/google";
import { NextApiRequest, NextApiResponse } from "next/types";

// Define your authentication options
const authOptions: NextAuthOptions = {
  adapter: PrismaAdapter(prisma),
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID as string,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET as string,
    }),
  ],
};

// Define a function to handle requests to this route
export default async (req: NextApiRequest, res: NextApiResponse) => {
  try {
    // Pass the request and response to the NextAuth handler along with the authentication options
    await NextAuth(req, res, authOptions);
  } catch (error) {
    // Handle errors if any
    console.error("Error during authentication:", error);
    res.status(500).end("Error during authentication");
  }
};
