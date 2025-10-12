

export async function threadPool(args: any[], func: (data: any) => any, limit = 4) {
  const pool = [];
  let i = 0;

  async function run() {
    while (i < args.length) {
      const url = args[i++];
      await func(url);
    }
  }

  for (let j = 0; j < limit; j++) {
    pool.push(run());
  }

  await Promise.all(pool);
}