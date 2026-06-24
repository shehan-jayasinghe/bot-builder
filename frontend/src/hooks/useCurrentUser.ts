import { useAuth } from "@clerk/clerk-react";
import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";

import { getMe } from "../api/auth";
import { setAuthTokenGetter } from "../api/client";

export function useCurrentUser() {
  const { isSignedIn, getToken, isLoaded } = useAuth();

  useEffect(() => {
    if (isSignedIn) {
      setAuthTokenGetter(() => getToken());
      return;
    }
    setAuthTokenGetter(async () => null);
  }, [getToken, isSignedIn]);

  return useQuery({
    queryKey: ["currentUser"],
    queryFn: async () => {
      setAuthTokenGetter(() => getToken());
      return getMe();
    },
    enabled: isLoaded && Boolean(isSignedIn),
    retry: false,
  });
}
