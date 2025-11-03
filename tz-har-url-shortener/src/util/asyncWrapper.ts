

export async function asyncWrapper<T>(
  callback: () => Promise<T>
): Promise<{ data: T | null; error: unknown }> {
  try {
    const data = await callback()
    return { data, error: null }
  } catch (error) {
    return { data: null, error }
  }
}